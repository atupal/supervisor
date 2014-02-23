# -*- Mode: Python -*-
#
#       Author: atupal <me@atupal.org>

RCS_ID = '$Id: rest_handler.py,v 1.8 2013/12/31 18:15:45 akuchling Exp $'

# standard python modules
import mimetypes
import re
import stat
import string

# medusa modules
from medusa import http_date
from medusa import http_server
from medusa import status_handler
from medusa import producers

#from supervisor.xmlrpc import SystemNamespaceRPCInterface
#from supervisor.xmlrpc import RootRPCInterface
#from supervisor.xmlrpc import Faults
#from supervisor.xmlrpc import RPCError
#
#from supervisor.rpcinterface import SupervisorNamespaceRPCInterface

unquote = http_server.unquote

# This is the 'restful' handler. It implements the restful api  I need
# For example: use http api replace the default rpc interfaceo.
# use github http hook to perceive the change of git repo code.

from medusa.counter import counter

class rest_handler:

    valid_commands = ['GET', 'HEAD', 'POST']

    IDENT = 'Restful api Handler'

    path = '/api'

    def __init__ (self, supervisord):
        self.supervisord = supervisord
        # count total hits
        self.hit_counter = counter()

    hit_counter = 0

    def __repr__ (self):
        return '<%s (%s hits) at %x>' % (
                self.IDENT,
                self.hit_counter,
                id (self)
                )

    def match (self, request):
        return request.uri.startswith(self.path)

    def handle_request (self, request):

        if request.command not in self.valid_commands:
            request.error (400) # bad request
            return

        self.hit_counter.increment()

        path, params, query, fragment = request.split_uri()
        repo = None
        if query:
          import urlparse
          qs = urlparse.parse_qs(query[1:])
          if qs.get('repo'):
            repo = qs.get('repo')[0]

        if '%' in path:
            path = unquote (path)

        # strip off all leading slashes
        while path and path[0] == '/':
            path = path[1:]

        class ViewContext:
            def __init__(self, **kw):
                self.__dict__.update(kw)

        context = ViewContext(template='ui/status.html',
                              request = request,
                              form = {
                                #'processname': 'nodeblog',
                                'processname': repo if repo else 'nodeblog',
                                'action': 'restart',
                                },
                              response = {
                                'headers': {},
                                },
                              supervisord=self.supervisord)
        from supervisor.web import StatusView
        from supervisor.web import DeferredWebProducer
        view = StatusView(context)
        pushproducer = request.channel.push_with_producer
        pushproducer(DeferredWebProducer(request, view))

        request['Content-Length'] = 2
        request['Content-Type'] = 'text/plain'


        request.push('ok')
        request.done()

    def status (self):
        return producers.simple_producer (
                '<li>%s' % status_handler.html_repr (self)
                + '<ul>'
                + '  <li><b>Total Hits:</b> %s'                 % self.hit_counter
                + '</ul>'
                )

    def make_callback(self, namespec=None, action=None):
        from supervisor.http import NOT_DONE_YET

        from supervisor.options import split_namespec

        from supervisor.xmlrpc import SystemNamespaceRPCInterface
        from supervisor.xmlrpc import RootRPCInterface
        from supervisor.xmlrpc import Faults
        from supervisor.xmlrpc import RPCError
        
        from supervisor.rpcinterface import SupervisorNamespaceRPCInterface
        main =   ('supervisor', SupervisorNamespaceRPCInterface(self.supervisord))
        system = ('system', SystemNamespaceRPCInterface([main]))

        rpcinterface = RootRPCInterface([main, system])

        if action:

            if action == 'refresh':
                def donothing():
                    message = 'Page refreshed at %s' % time.ctime()
                    return message
                donothing.delay = 0.05
                return donothing

            elif action == 'stopall':
                callback = rpcinterface.supervisor.stopAllProcesses()
                def stopall():
                    if callback() is NOT_DONE_YET:
                        return NOT_DONE_YET
                    else:
                        return 'All stopped at %s' % time.ctime()
                stopall.delay = 0.05
                return stopall

            elif action == 'restartall':
                callback = rpcinterface.system.multicall(
                    [ {'methodName':'supervisor.stopAllProcesses'},
                      {'methodName':'supervisor.startAllProcesses'} ] )
                def restartall():
                    result = callback()
                    if result is NOT_DONE_YET:
                        return NOT_DONE_YET
                    return 'All restarted at %s' % time.ctime()
                restartall.delay = 0.05
                return restartall

            elif namespec:
                def wrong():
                    return 'No such process named %s' % namespec
                wrong.delay = 0.05
                group_name, process_name = split_namespec(namespec)
                group = self.supervisord.process_groups.get(group_name)
                if group is None:
                    return wrong
                process = group.processes.get(process_name)
                if process is None:
                    return wrong

                elif action == 'stop':
                    callback = rpcinterface.supervisor.stopProcess(namespec)
                    def stopprocess():
                        result = callback()
                        if result is NOT_DONE_YET:
                            return NOT_DONE_YET
                        return 'Process %s stopped' % namespec
                    stopprocess.delay = 0.05
                    return stopprocess

                elif action == 'restart':
                    callback = rpcinterface.system.multicall(
                        [ {'methodName':'supervisor.stopProcess',
                           'params': [namespec]},
                          {'methodName':'supervisor.startProcess',
                           'params': [namespec]},
                          ]
                        )
                    def restartprocess():
                        result = callback()
                        if result is NOT_DONE_YET:
                            return NOT_DONE_YET
                        return 'Process %s restarted' % namespec
                    restartprocess.delay = 0.05
                    return restartprocess

                elif action == 'start':
                    try:
                        callback = rpcinterface.supervisor.startProcess(
                            namespec)
                    except RPCError, e:
                        if e.code == Faults.SPAWN_ERROR:
                            def spawnerr():
                                return 'Process %s spawn error' % namespec
                            spawnerr.delay = 0.05
                            return spawnerr
                    def startprocess():
                        if callback() is NOT_DONE_YET:
                            return NOT_DONE_YET
                        return 'Process %s started' % namespec
                    startprocess.delay = 0.05
                    return startprocess

                elif action == 'clearlog':
                    callback = rpcinterface.supervisor.clearProcessLog(
                        namespec)
                    def clearlog():
                        return 'Log for %s cleared' % namespec
                    clearlog.delay = 0.05
                    return clearlog
