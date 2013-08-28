'''
Created on Jul 31, 2013

@author: openstack
'''

def format_dict(d, tab=0):
    try:
        s = ['{\n']
        for k,v in d.items():
            if isinstance(v, dict):
                v = format_dict(v, tab+1)
            else:
                v = repr(v)

            s.append('%s%r: %s,\n' % ('  '*tab, k, v))
        s.append('%s}' % ('  '*tab))
        return ''.join(s)
    except Exception as e:
        print e
