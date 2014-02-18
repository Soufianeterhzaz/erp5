# -*- coding: utf-8 -*-
# Code based on python-memcached-1.53
try:
    from memcache import _Host, Client, _Error, _ConnectionDeadError
except ImportError:
    pass
else:
    _Host._SOCKET_TIMEOUT = 10 # wait more than 3s is safe

    # Client._get() should raises an Exception instead of returning
    # None, in case of connection errors or missing values.
    class MemcachedConnectionError(Exception):
        pass
    Client.MemcachedConnectionError = MemcachedConnectionError

    import socket
    def _get(self, cmd, key):
        if self.do_check_key:
            self.check_key(key)
        server, key = self._get_server(key)
        if not server:
            # (patch)
            # return None
            raise MemcachedConnectionError

        def _unsafe_get():
            self._statlog(cmd)

            try:
                server.send_cmd("%s %s" % (cmd, key))
                rkey = flags = rlen = cas_id = None

                if cmd == 'gets':
                    rkey, flags, rlen, cas_id, = self._expect_cas_value(server,
                            raise_exception=True)
                    if rkey and self.cache_cas:
                        self.cas_ids[rkey] = cas_id
                else:
                    rkey, flags, rlen, = self._expectvalue(server,
                            raise_exception=True)

                if not rkey:
                    # (patch)
                    # return None
                    raise KeyError
                try:
                    value = self._recv_value(server, flags, rlen)
                finally:
                    server.expect("END", raise_exception=True)
            except (_Error, socket.error), msg:
                if isinstance(msg, tuple): msg = msg[1]
                server.mark_dead(msg)
                # (patch)
                # return None
                raise MemcachedConnectionError

            return value

        try:
            return _unsafe_get()
        except _ConnectionDeadError:
            # retry once
            try:
                if server.connect():
                    return _unsafe_get()
                # (patch)
                # return None
                raise MemcachedConnectionError
            except (_ConnectionDeadError, socket.error), msg:
                server.mark_dead(msg)
            # (patch)
            # return None
            raise MemcachedConnectionError

    Client._get = _get
