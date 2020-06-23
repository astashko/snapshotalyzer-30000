import boto3
import botocore
import click

session = boto3.Session(profile_name='shotty')
ec2 = session.resource('ec2')

def get_instances(project):
    if project:
        filters = [{'Name': 'tag:Project', 'Values': [project]}]
        return ec2.instances.filter(Filters = filters)
    else:
        return ec2.instances.all()

@click.group()
def cli():
    """Shotty manages snapshots"""

@cli.group()
def instances():
    """Commands for instances"""

@instances.command('list')
@click.option('--project', default = None,
    help = "Only instances for project (tag Project:<name>)")
def list_instances(project):
    "List EC2 instances"
    
    for i in get_instances(project):
        tags = {t['key']: t['Value'] for t in i.tags or []}
        print(', '.join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state['Name'],
            i.public_dns_name,
            tags.get('Project', '<no project>')
        )))
    
    return

@instances.command('stop')
@click.option('--project', default = None,
    help = "Only instances for project (tag Project:<name>)")
def stop_instances(project):
    "Stop EC2 instances"

    for i in get_instances(project):
        print("Stopping {0}...".format(i.id))
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
            print(" Could not stop {0}. ".format(i.id) + str(e))

    return

@instances.command('start')
@click.option('--project', default = None,
    help = "Only instances for project (tag Project:<name>)")
def start_instances(project):
    "Start EC2 instances"

    for i in get_instances(project):
        print("Starting {0}...".format(i.id))
        try:
            i.start()
        except botocore.exceptions.ClientError as e:
            print(" Could not start {0}. ".format(i.id) + str(e))

    return

@instances.command('snapshot', help = 'Create snapshots of all volumes')
@click.option('--project', default = None,
    help = "Only instances for project (tag Project:<name>)")
def create_snapshots(project):
    "Create snapshots for EC2 instances"

    for i in get_instances(project):
        print("Stopping {0}...".format(i.id))
        i.stop()
        i.wait_until_stopped()
        
        for v in i.volumes.all():
            print("  Creating snapshot of {0}".format(v.id))
            v.crate_snapshot(Description = "Created by Snapshotalyzer 30000")
        
        print("Starting {0}...".format(i.id))
        i.start()
        i.wait_until_running()

    print('Jon''s done!')
    return

@cli.group()
def volumes():
    """Commands for volumes"""

@volumes.command('list')
@click.option('--project', default = None,
    help = "Only volumes from instances for project (tag Project:<name>)")
def list_volumes(project):
    "List EC2 volumes"

    instances = get_instances(project)

    for i in instances:
        for v in i.volumes.all():
            print(", ".join((
                v.id,
                i.id,
                v.state,
                str(v.size) + "GiB",
                v.encrypted and "Encrypted" or "Not Encrypted"
            )))
    
    return

@cli.group()
def snapshots():
    """Commands for snapshots"""

@snapshots.command('list')
@click.option('--project', default = None,
    help = "Only snapshots from instances for project (tag Project:<name>)")
@click.option('--all', 'list_all', default = False, is_flag = True,
    help = "List all snapshots for each volume, not just thr most recent")
def list_snapshots(project, list_all):
    "List EC2 snapshots"

    instances = get_instances(project)

    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print(", ".join((
                    s.id,
                    v.id,
                    i.id,
                    v.state,
                    s.progress,
                    s.start_time.strftime("%c")
                )))

                if not list_all and s.state == "completed": break
    
    return

if __name__ == '__main__':
    cli()