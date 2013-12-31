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

unquote = http_server.unquote

# This is the 'default' handler.  it implements the base set of
# features expected of a simple file-delivering HTTP server.  file
# services are provided through a 'filesystem' object, the very same
# one used by the FTP server.
#
# You can replace or modify this handler if you want a non-standard
# HTTP server.  You can also derive your own handler classes from
# it.
#
# support for handling POST requests is available in the derived
# class <default_with_post_handler>, defined below.
#

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

        if '%' in path:
            path = unquote (path)

        # strip off all leading slashes
        while path and path[0] == '/':
            path = path[1:]

        request.push('ok')
        request['Content-Length'] = 2
        request['Content-Type'] = 'text/plain'

        request.done()

    def status (self):
        return producers.simple_producer (
                '<li>%s' % status_handler.html_repr (self)
                + '<ul>'
                + '  <li><b>Total Hits:</b> %s'                 % self.hit_counter
                + '</ul>'
                )
