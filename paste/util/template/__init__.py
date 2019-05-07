try:
    from tempita import *
    from tempita import paste_script_template_renderer
except ImportError:
    from _template import *
    from _template import paste_script_template_renderer
