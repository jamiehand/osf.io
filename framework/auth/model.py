# -*- coding: utf-8 -*-
import itertools
import datetime as dt
from pytz import utc
from framework.bcrypt import generate_password_hash, check_password_hash
from framework import StoredObject, fields,  Q
from bson import ObjectId

from framework.search import solr

from website import settings

name_formatters = {
   'long': lambda user: user.fullname,
   'surname': lambda user: user.surname,
   'initials': lambda user: u'{surname}, {initial}.'.format(
       surname=user.surname,
       initial=user.given_name_initial
   ),
}

class User(StoredObject):
    _id = fields.StringField(primary=True)

    username = fields.StringField()
    password = fields.StringField()
    fullname = fields.StringField()
    is_registered = fields.BooleanField()
    is_claimed = fields.BooleanField()
    verification_key = fields.StringField()
    emails = fields.StringField(list=True)
    email_verifications = fields.DictionaryField()
    aka = fields.StringField(list=True)
    date_registered = fields.DateTimeField()#auto_now_add=True)
    # Watched nodes are stored via a list of WatchConfigs
    watched = fields.ForeignField("WatchConfig", list=True, backref="watched")

    api_keys = fields.ForeignField('apikey', list=True, backref='keyed')

    _meta = {'optimistic' : True}

    def set_password(self, raw_password):
        '''Set the password for this user to the hash of ``raw_password``.'''
        self.password = generate_password_hash(raw_password)
        return None

    def check_password(self, raw_password):
        '''Return a boolean of whether ``raw_password`` was correct.'''
        return check_password_hash(self.password, raw_password)

    @property
    def surname(self):
        """
        The user's preferred surname or family name, as they would prefer it to
        appear in print.
        e.g.: "Jeffrey Spies" would be "Spies".
        """
        # TODO: Give users the ability to specify this via their profile
        return self.fullname.split(' ')[-1]

    @property
    def given_name(self):
        """
        The user's preferred given name, as they would be addressed personally.
        e.g.: "Jeffrey Spies" would be "Jeffrey" (or "Jeff")
        """
        # TODO: Give users the ability to specify this via their profile
        return self.fullname.split(' ')[0]

    @property
    def given_name_initial(self):
        """
        The user's preferred initialization of their given name.

        Some users with common names may choose to distinguish themselves from
        their colleagues in this way. For instance, there could be two
        well-known researchers in a single field named "Robert Walker".
        "Walker, R" could then refer to either of them. "Walker, R.H." could
        provide easy disambiguation.

        NOTE: The internal representation for this should never end with a
              period. "R" and "R.H" would be correct in the prior case, but
              "R.H." would not.
        """
        #TODO: Give users the ability to specify this via their profile.
        return self.given_name[0]

    @property
    def profile_url(self):
        return '/profile/{}/'.format(self._id)

    def get_summary(self, formatter='long'):
        return {
            'user_fullname': self.fullname,
            'user_profile_url': self.profile_url,
            'user_display_name': name_formatters[formatter](self),
        }

    def save(self, *args, **kwargs):
        rv = super(User, self).save(*args, **kwargs)
        self.update_solr()
        return rv

    def update_solr(self):
        if not settings.use_solr:
            return
        solr.update_user(self)

    @classmethod
    def find_by_email(cls, email):
        try:
            user = cls.find_one(
                Q('emails', 'eq', email)
            )
            return [user]
        except:
            return []

    def watch(self, watch_config, save=False):
        '''Watch a node by adding its WatchConfig to this user's ``watched``
        list. Raises ``ValueError`` if the node is already watched.

        :param watch_config: The WatchConfig to add.
        :param save: Whether to save the user.
        '''
        watched_nodes = [each.node for each in self.watched]
        if watch_config.node in watched_nodes:
            raise ValueError("Node is already being watched.")
        watch_config.save()
        self.watched.append(watch_config)
        if save:
            self.save()
        return None

    def unwatch(self, watch_config, save=False):
        '''Unwatch a node by removing its WatchConfig from this user's ``watched``
        list. Raises ``ValueError`` if the node is not already being watched.

        :param watch_config: The WatchConfig to remove.
        :param save: Whether to save the user.
        '''
        for each in self.watched:
            if watch_config.node._id == each.node._id:
                each.__class__.remove_one(each)
                if save:
                    self.save()
                return None
        raise ValueError('Node not being watched.')

    def is_watching(self, node):
        '''Return whether a not a user is watching a Node.'''
        watched_node_ids = set([config.node._id for config in self.watched])
        return node._id in watched_node_ids

    def get_recent_log_ids(self, since=None):
        '''Return a generator of recent logs' ids.

        :param since: A datetime specifying the oldest time to retrieve logs
        from. If ``None``, defaults to 60 days before today. Must be a tz-aware
        datetime because PyMongo's generation times are tz-aware.

        :rtype: generator of log ids (strings)
        '''
        log_ids = []
        # Default since to 60 days before today if since is None
        # timezone aware utcnow
        utcnow = dt.datetime.utcnow().replace(tzinfo=utc)
        since_date = since if since else (utcnow - dt.timedelta(days=60))
        for config in self.watched:
            # Extract the timestamps for each log from the log_id (fast!)
            # The first 4 bytes of Mongo's ObjectId encodes time
            # This prevents having to load each Log Object and access their
            # date fields
            node_log_ids = [log_id for log_id in config.node.logs._to_primary_keys()
                                   if ObjectId(log_id).generation_time > since_date]
            # Log ids in reverse chronological order
            log_ids = _merge_into_reversed(log_ids, node_log_ids)
        return (l_id for l_id in log_ids)


def _merge_into_reversed(*iterables):
    '''Merge multiple sorted inputs into a single output in reverse order.
    '''
    return sorted(itertools.chain(*iterables), reverse=True)
