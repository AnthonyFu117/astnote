#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-

import sys
import json
import hashlib
import random
import string
import glob
import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.options
import minifier
from   configs.config   import configs

def get_authcode(mode,name,amount=3):
    return str(int(hashlib.md5((mode + ':' + name + ':ant').encode()).hexdigest(),16))[-amount:]

class base_handler(tornado.web.RequestHandler):
    def get_template_namespace(self):
        ns = super(base_handler, self).get_template_namespace()
        ns.update({
            'root': configs.root,
            'firebase': configs.firebase,
            'min': 'min.' if configs.minify else ''
        })
        return ns

class index_handler(base_handler):
    def get(self):
        self.render('index.html')

class random_handler(base_handler):
    def get(self,mode):
        name = ''.join([random.choice(string.digits) for x in range(6)])
        authcode = get_authcode(mode,name)
        self.redirect(configs.root+'/{mode}/{name}/{auth}'.format(mode=mode,name=name,auth=authcode))

class create_handler(base_handler):
    def get(self,mode,name):
        authcode = get_authcode(mode,name)
        self.redirect(configs.root+'/{mode}/{name}/{auth}'.format(mode=mode,name=name,auth=authcode))

class editors_handler(base_handler):
    def get(self,mode,name,authcode):
        if authcode == get_authcode(mode,name):
            self.render('editor.html',mode=mode,name=name)
        else:
            self.render('error.html',error_code='Auth Failed',error_display='Maybe you got a wrong url.')

class not_found_handler(base_handler):
    def get(self):
        self.render('error.html',error_code='404',error_display='Page Not Found')

def globset(pattern):
    return set(glob.glob(pattern))

def minify():
    targets = set(glob.glob('static/*.js') + glob.glob('static/*.css')) - set(glob.glob('static/*.min.js') + glob.glob('static/*.min.css'))
    for t in targets:
        minifier.minify(t)
    print('Minify Finished')

if __name__ == '__main__':
    if configs.minify:
        minify()
    args = sys.argv
    args.append("--log_file_prefix=logs/web.log")
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[
            (r'/',index_handler),
            (r'/random/(r|t|c|m)',random_handler),
            (r'/ant/(r|t|c|m)/(\w+)',create_handler),
            (r'/(r|t|c|m)/(\w+)/(\w+)',editors_handler),
            (r'.*',not_found_handler)
        ],
        template_path='template',
        static_path='static',
        debug=True
    )
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(configs.port)
    tornado.ioloop.IOLoop.instance().start()