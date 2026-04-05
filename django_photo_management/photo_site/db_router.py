class OracleRouter:
    """USE_ORACLE=True 时把部分应用路由到 Oracle（见 settings.DATABASE_ROUTERS）。"""

    route_app_labels = {'photo_access', 'users', 'photos', 'configs', 'audit'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'oracle'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'oracle'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'oracle':
            return app_label in self.route_app_labels
        if app_label in self.route_app_labels:
            return False
        return None
