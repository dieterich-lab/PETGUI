'''LDAP'''
from ldap3 import Server, Connection, ALL, Tls, AUTO_BIND_TLS_BEFORE_BIND, core
from ssl import PROTOCOL_TLSv1_2

class LdapService:
    def __init__(self):
        pass

    def authenticate_ldap(username: str, password: str):
        LDAP_SERVER = 'ldap://ldap2.dieterichlab.org'
        CA_FILE = 'DieterichLab_CA.pem'
        USER_BASE = 'dc=dieterichlab,dc=org'
        LDAP_SEARCH_FILTER = '({name_attribute}={name})'
        try:
            tls = Tls(ca_certs_file=CA_FILE, version=PROTOCOL_TLSv1_2)
            server = Server(LDAP_SERVER, get_info=ALL, tls=tls)
            conn = Connection(server, auto_bind=AUTO_BIND_TLS_BEFORE_BIND, raise_exceptions=True)
            conn.bind()
            conn.search(USER_BASE, LDAP_SEARCH_FILTER.format(name_attribute="uid", name=username))
            if conn.result['result'] == 0:
                user_dn = conn.response[0]['dn']
                try:
                    conn = Connection(server, user_dn, password, auto_bind=AUTO_BIND_TLS_BEFORE_BIND)
                    return True
                except core.exceptions.LDAPBindError:
                    print("User authentication failed.")
                    return False
            else:
                return False
        except Exception as e:
            print(str(e))
            return False
