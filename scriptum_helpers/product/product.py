import uVault
from digitalocean import space as Space
from digitalocean import sshkey
from digitalocean import droplet as Droplet
from digitalocean import app as App

from jinja2 import Environment, FileSystemLoader, Undefined, StrictUndefined
from .jinja2 import S3Loader

import yaml


class Product:

    def __init__(self, customer, environment, name, region="fra1"):
        self.name = name
        self.env = environment
        self.region = region
        self._keys = []

        self.key = "/".join((customer, environment, name))
        if True:
            self.backend, self.reader = uVault.get_readers("local", self.key)
            loader=FileSystemLoader("products/")
        else:
            self.backend, self.reader = uVault.get_readers("storage", self.key)
            loader=S3Loader("products/")

        self.j2 = Environment(
                loader=loader,
                undefined=StrictUndefined
                )

        # Read descriptor
        self.backend.descriptor(self)

        # Check for mandatory items
        assert self.repository, "No repository defined"

        self.template = "blueprints/%s.j2" % getattr(self, "blueprint", self.name)
        self.config = getattr(self, "config", "%s/config.j2" % self.name)

        self.configuration = self.backend.config(self) if self.config else {}

        if "app" in self.configuration:
            self.configuration.remove("app")
            self.configuration.add("App")

        self.requirements = set()
        if getattr(self, "droplets", None):
            self.requirements.update(self.droplets)
        else:
            self.droplets = []
        if getattr(self, "storage", None):
            self.requirements.add("DOSpaces")

        if self.config:
            self.configuration.difference_update(self.requirements)

        if getattr(self, "external", None):
            acc = {}
            for kv in self.external.items():
                for v in kv[1]:
                    acc[v] = kv[0]
            self.external = acc
        else:
            self.external = {}

    def add(self, name, value):
        setattr(self, name, value)

    def settings(self):

        if not self.configuration:
            return {}

        conf = {}
        for configuration in self.configuration:
            if configuration in self.external:
                conf[configuration.lower()] = self.reader.sibling(self.external[configuration], configuration)
            else:
                conf[configuration.lower()] = self.reader.finder(configuration)

        for requirement in self.requirements:
            if requirement.lower() in conf:
                print("WARNING: Fixed configuratione exits for '%s'" % requirement)
            conf[requirement.lower()] = {}

        return conf

    def render_config(self, **kwargs):
        return self.j2.get_template(self.config).render(**kwargs)

    def render_template(self, **kwargs):
        return self.j2.get_template(self.template).render(**kwargs)

    def __str__(self):
        config = {key: getattr(self, key) for key in self._keys}
        config.update({
          "requirements": self.requirements,
          "template": self.template,
          "config": self.config,
          "configuration": self.configuration
          })
        return str(config)

    def create(self, project_name, project_id, conf):

        if "app" in self.configuration:
            # When app configuration refers to itself, first we create as front-only
            # so that live url is available to generate configuration
            spec = self.render_template(
                product=self.name,
                version=version,
                environment=self.env,
                region=self.region,
                repository=self.repository.lower(),
                variables=conf,
                config=""
            )
            spec = yaml.load(spec, Loader=yaml.SafeLoader)
            spec["name"] = spec["name"].lower()

            # Keep only static site
            for key in "envs", "services", "workers":
                spec.pop(key, None)
            spec["ingress"]["rules"] = [rule
                                        for rule in spec["ingress"]["rules"]
                                        if rule["match"]["path"]["prefix"] == "/"]

            app = App.new(spec)
            app.instantiate(project_id, self.reader)
            app.settings(conf)

        if self.droplets:
            key_id, privkey = sshkey.new(project_name)

        for asset in self.droplets:
            name = "%s-%s-%s" % (self.name, self.env, asset.lower())
            asset = Droplet.new(asset, name, key_id, self.region)
            asset.instantiate(project_id, self.reader, privkey)
            asset.settings(conf)

        if "DOSpaces" in self.requirements:
            name = "%s-%s" % (self.name.lower(), self.env)
            space = Space.new(name, self.region)
            space.instantiate(project_id, self.reader, True)
            space.settings(conf)
