import os
from django.core.checks import Error, Warning, register
from django.conf import settings


@register()
def staging_dir_check(app_configs, **kwargs):
    if not hasattr(settings, 'BAG_STAGING_DIR'):
        return [Error(
                'BAG_STAGING_DIR is not defined.',
                hint='Add a directory (/tmp/bag_staging) where bags can be '
                     'packed/unpacked',
                obj=settings,
                id='api.E001',
                )]

    if not os.path.exists(os.path.dirname(settings.BAG_STAGING_DIR)):
        return [Error(
                'BAG_STAGING_DIR parent directory does not exist.',
                hint='Ensure this is a good place to stage bags and create '
                     'the {} directory.'.format(settings.BAG_STAGING_DIR),
                obj=settings,
                id='api.E002',
                )]

    if not os.path.exists(settings.BAG_STAGING_DIR):
        os.mkdir(settings.BAG_STAGING_DIR)
        return [Warning(
            'Creating bag staging directory at {}'.format(
                settings.BAG_STAGING_DIR
            ),
            id='api.W001'
        )]

    return []
