# -*- coding: utf-8 -*-

# ----------------------------------------------------------------------
# NOTE: The default values of the settings are defined in
# openstack_dashboard/defaults.py. Previously most available settings
# were listed in this example file, but it is no longer true.
# For available settings, see openstack_dashboard/defaults.py and
# the horizon setting reference found at
# https://docs.openstack.org/horizon/latest/configuration/settings.html.
#
# Django related settings and HORIZON_CONFIG still exist here.
# Keep in my mind that they will be revisit in upcoming releases.
# ----------------------------------------------------------------------

import os

from django.utils.translation import gettext_lazy as _

from horizon.utils import secret_key

from openstack_dashboard.settings import HORIZON_CONFIG

DEBUG = False

# This setting controls whether or not compression is enabled. Disabling
# compression makes Horizon considerably slower, but makes it much easier
# to debug JS and CSS changes
#COMPRESS_ENABLED = not DEBUG

# This setting controls whether compression happens on the fly, or offline
# with `python manage.py compress`
# See https://django-compressor.readthedocs.io/en/latest/usage/#offline-compression
# for more information
#COMPRESS_OFFLINE = not DEBUG

# If horizon is running in production (DEBUG is False), set this
# with the list of host/domain names that the application can serve.
# For more information see:
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
#ALLOWED_HOSTS = ['horizon.example.com', ]

# Set SSL proxy settings:
# Pass this header from the proxy after terminating the SSL,
# and don't forget to strip it from the client's request.
# For more information see:
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
#SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# If Horizon is being served through SSL, then uncomment the following two
# settings to better secure the cookies from security exploits
#CSRF_COOKIE_SECURE = True
#SESSION_COOKIE_SECURE = True

# If provided, a "Report Bug" link will be displayed in the site header
# which links to the value of this setting (ideally a URL containing
# information on how to report issues).
#HORIZON_CONFIG["bug_url"] = "http://bug-report.example.com"

# Show backdrop element outside the modal, do not close the modal
# after clicking on backdrop.
#HORIZON_CONFIG["modal_backdrop"] = "static"

# Specify a regular expression to validate user passwords.
#HORIZON_CONFIG["password_validator"] = {
#    "regex": '.*',
#    "help_text": _("Your password does not meet the requirements."),
#}

# Turn off browser autocompletion for forms including the login form and
# the database creation workflow if so desired.
#HORIZON_CONFIG["password_autocomplete"] = "off"

# Setting this to True will disable the reveal button for password fields,
# including on the login form.
#HORIZON_CONFIG["disable_password_reveal"] = False

LOCAL_PATH = os.path.dirname(os.path.abspath(__file__))

# Set custom secret key:
# You can either set it to a specific value or you can let horizon generate a
# default secret key that is unique on this machine, e.i. regardless of the
# amount of Python WSGI workers (if used behind Apache+mod_wsgi): However,
# there may be situations where you would want to set this explicitly, e.g.
# when multiple dashboard instances are distributed on different machines
# (usually behind a load-balancer). Either you have to make sure that a session
# gets all requests routed to the same dashboard instance or you set the same
# SECRET_KEY for all of them.
SECRET_KEY = secret_key.generate_or_read_from_file('/var/lib/openstack-dashboard/secret_key')

# We recommend you use memcached for development; otherwise after every reload
# of the django development server, you will have to login again. To use
# memcached set CACHES to something like below.
# For more information, see
# https://docs.djangoproject.com/en/1.11/topics/http/sessions/.

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': '179.20.3.81:11211',
    },
}

#CACHES = {
#    'default': {
#        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#    }
#}

# If you use ``tox -e runserver`` for developments,then configure
# SESSION_ENGINE to django.contrib.sessions.backends.signed_cookies
# as shown below:
#SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
#SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_ENGINE = "django.contrib.sessions.backends.cache"


# Send email to the console by default
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# Or send them to /dev/null
#EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

# Configure these for your outgoing email host
#EMAIL_HOST = 'smtp.my-company.com'
#EMAIL_PORT = 25
#EMAIL_HOST_USER = 'djangomail'
#EMAIL_HOST_PASSWORD = 'top-secret!'

OPENSTACK_HOST = "179.20.3.81"
#OPENSTACK_KEYSTONE_URL = "http://%s/identity/v3" % OPENSTACK_HOST
OPENSTACK_KEYSTONE_URL = "http://179.20.3.81:5000/v3"

# The timezone of the server. This should correspond with the timezone
# of your entire OpenStack installation, and hopefully be in UTC.
TIME_ZONE = "Asia/Shanghai"

# Change this patch to the appropriate list of tuples containing
# a key, label and static directory containing two files:
# _variables.scss and _styles.scss
#AVAILABLE_THEMES = [
#    ('default', 'Default', 'themes/default'),
#    ('material', 'Material', 'themes/material'),
#    ('example', 'Example', 'themes/example'),
#]

LOGGING = {
    'version': 1,
    # When set to True this will disable all logging except
    # for loggers specified in this configuration dictionary. Note that
    # if nothing is specified here and disable_existing_loggers is True,
    # django.db.backends will still log unless it is disabled explicitly.
    'disable_existing_loggers': False,
    # If apache2 mod_wsgi is used to deploy OpenStack dashboard
    # timestamp is output by mod_wsgi. If WSGI framework you use does not
    # output timestamp for logging, add %(asctime)s in the following
    # format definitions.
    'formatters': {
        'console': {
            'format': '%(levelname)s %(name)s %(message)s'
        },
        'operation': {
            # The format of "%(message)s" is defined by
            # OPERATION_LOG_OPTIONS['format']
            'format': '%(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            # Set the level to "DEBUG" for verbose output logging.
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
        'operation': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'operation',
        },
    },
    'loggers': {
        'horizon': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'horizon.operation_log': {
            'handlers': ['operation'],
            'level': 'INFO',
            'propagate': False,
        },
        'openstack_dashboard': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'novaclient': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'cinderclient': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'keystoneauth': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'keystoneclient': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'glanceclient': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'neutronclient': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'swiftclient': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'oslo_policy': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'openstack_auth': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # VariableDoesNotExist error in the debug level from django.template
        # is VERY noisy and it is output even for valid cases,
        # so set the default log level of django.template to INFO.
        'django.template': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        # Logging from django.db.backends is VERY verbose, send to null
        # by default.
        'django.db.backends': {
            'handlers': ['null'],
            'propagate': False,
        },
        'requests': {
            'handlers': ['null'],
            'propagate': False,
        },
        'urllib3': {
            'handlers': ['null'],
            'propagate': False,
        },
        'chardet.charsetprober': {
            'handlers': ['null'],
            'propagate': False,
        },
        'iso8601': {
            'handlers': ['null'],
            'propagate': False,
        },
        'scss': {
            'handlers': ['null'],
            'propagate': False,
        },
    },
}

# 'direction' should not be specified for all_tcp/udp/icmp.
# It is specified in the form.
SECURITY_GROUP_RULES = {
    'all_tcp': {
        'name': _('All TCP'),
        'ip_protocol': 'tcp',
        'from_port': '1',
        'to_port': '65535',
    },
    'all_udp': {
        'name': _('All UDP'),
        'ip_protocol': 'udp',
        'from_port': '1',
        'to_port': '65535',
    },
    'all_icmp': {
        'name': _('All ICMP'),
        'ip_protocol': 'icmp',
        'from_port': '-1',
        'to_port': '-1',
    },
    'ssh': {
        'name': 'SSH',
        'ip_protocol': 'tcp',
        'from_port': '22',
        'to_port': '22',
    },
    'smtp': {
        'name': 'SMTP',
        'ip_protocol': 'tcp',
        'from_port': '25',
        'to_port': '25',
    },
    'dns': {
        'name': 'DNS',
        'ip_protocol': 'tcp',
        'from_port': '53',
        'to_port': '53',
    },
    'http': {
        'name': 'HTTP',
        'ip_protocol': 'tcp',
        'from_port': '80',
        'to_port': '80',
    },
    'pop3': {
        'name': 'POP3',
        'ip_protocol': 'tcp',
        'from_port': '110',
        'to_port': '110',
    },
    'imap': {
        'name': 'IMAP',
        'ip_protocol': 'tcp',
        'from_port': '143',
        'to_port': '143',
    },
    'ldap': {
        'name': 'LDAP',
        'ip_protocol': 'tcp',
        'from_port': '389',
        'to_port': '389',
    },
    'https': {
        'name': 'HTTPS',
        'ip_protocol': 'tcp',
        'from_port': '443',
        'to_port': '443',
    },
    'smtps': {
        'name': 'SMTPS',
        'ip_protocol': 'tcp',
        'from_port': '465',
        'to_port': '465',
    },
    'imaps': {
        'name': 'IMAPS',
        'ip_protocol': 'tcp',
        'from_port': '993',
        'to_port': '993',
    },
    'pop3s': {
        'name': 'POP3S',
        'ip_protocol': 'tcp',
        'from_port': '995',
        'to_port': '995',
    },
    'ms_sql': {
        'name': 'MS SQL',
        'ip_protocol': 'tcp',
        'from_port': '1433',
        'to_port': '1433',
    },
    'mysql': {
        'name': 'MYSQL',
        'ip_protocol': 'tcp',
        'from_port': '3306',
        'to_port': '3306',
    },
    'rdp': {
        'name': 'RDP',
        'ip_protocol': 'tcp',
        'from_port': '3389',
        'to_port': '3389',
    },
}

# Help URL can be made available for the client. To provide a help URL, edit the
# following attribute to the URL of your choice.
#HORIZON_CONFIG["help_url"] = "http://openstack.mycompany.org"

###############################################################################
# Ubuntu Settings
###############################################################################

# The default theme if no cookie is present
#DEFAULT_THEME = 'ubuntu'

# Default Ubuntu apache configuration uses /horizon as the application root.
WEBROOT='/horizon/'

# By default, validation of the HTTP Host header is disabled.  Production
# installations should have this set accordingly.  For more information
# see https://docs.djangoproject.com/en/dev/ref/settings/.
ALLOWED_HOSTS = ['*']

# Compress all assets offline as part of packaging installation
#COMPRESS_OFFLINE = True
#OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT = True
#OPENSTACK_KEYSTONE_DEFAULT_DOMAIN = 'Default'
# set [True] below if you are using self signed certificate
#OPENSTACK_SSL_NO_VERIFY = False
