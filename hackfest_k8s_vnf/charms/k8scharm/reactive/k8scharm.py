from charms.layer.caas_base import pod_spec_set
from charms.reactive import when, when_not, when_any
from charms.reactive.flags import set_flag, register_trigger

from charmhelpers.core.hookenv import (
    log,
    metadata,
    config,
    application_name,
)
from charms import layer


register_trigger(when='layer.docker-resource.ubuntu-image.changed',
                 clear_flag='k8scharm.configured')


@when_any('layer.docker-resource.ubuntu-image.failed')
def waiting_for_image():
    """Set status blocked

    Conditions:
        - ubuntu-image.failed
    """
    layer.status.blocked('Failed fetching Ubuntu image')


@when('layer.docker-resource.ubuntu-image.available')
@when_not('k8scharm.configured')
def configure():
    """Configure Ubuntu pod

    Conditions:
        - ubuntu-image.available
        - Not k8scharm.configured
    """
    layer.status.maintenance('Configuring ubuntu container')

    spec = make_pod_spec()
    log('set pod spec:\n{}'.format(spec))
    pod_spec_set(spec)

    set_flag('k8scharm.configured')


@when('k8scharm.configured')
def set_k8scharm_active():
    """Set k8scharm status active

    Conditions:
        - k8scharm.configured
    """
    layer.status.active('ready')


def make_pod_spec():
    """Make pod specification for Kubernetes

    Returns:
        pod_spec: Pod specification for Kubernetes
    """
    md = metadata()
    cfg = config()
    image_info = layer.docker_resource.get_info('ubuntu-image')
    with open('reactive/spec_template.yaml') as spec_file:
        pod_spec_template = spec_file.read()

    app_name = application_name()

    data = {
        'name': md.get('name'),
        'docker_image_path': image_info.registry_path,
        'docker_image_username': image_info.username,
        'docker_image_password': image_info.password,
        'application_name': app_name,
    }
    data.update(cfg)
    return pod_spec_template % data
