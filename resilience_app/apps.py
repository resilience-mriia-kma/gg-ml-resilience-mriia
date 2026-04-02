from django.apps import AppConfig

from resilience_app.container import ResilienceContainer


class ResilienceAppConfig(AppConfig):
    name = "resilience_app"
    container = ResilienceContainer()

    def ready(self):
        self.container.wire(modules=[".views"])
