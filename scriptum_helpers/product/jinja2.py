import scriptum_helpers.storage as storage
from jinja2 import BaseLoader, TemplateNotFound

class S3Loader(BaseLoader):

    def __init__(self, topdir):
        self.topdir = topdir

    def get_source(self, environment, template_name):
        try:
            template_content = storage.get(self.topdir + template_name)
            return template_content.decode("utf-8"), self.topdir+template_name, None
        except Exception as ex:
            raise TemplateNotFound("%s: %s" % (template_name, ex))
