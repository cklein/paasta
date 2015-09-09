import sys
import json
from behave import when, then

sys.path.append('../')
from paasta_tools.utils import _run
from paasta_tools.chronos_tools import compose_job_id


@when('I launch "{num_jobs}" "{state}" chronos jobs with service "{service}" with chronos instance "{job}" and differing tags')
def launch_jobs(context, num_jobs, state, service, job):
    client = context.chronos_client
    jobs = [{
        'async': False,
        'command': 'echo 1',
        'epsilon': 'PT15M',
        'name': compose_job_id(service, job, 'config%d' % x),
        'owner': 'paasta',
        'disabled': True,
        'schedule': 'R/2014-01-01T00:00:00Z/PT60M',
    } for x in range(0, int(num_jobs))]
    for job in jobs:
        try:
            client.add(job)
        except Exception:
            print 'Error creating test job: %s' % json.dumps(job)
            raise

    if state == "known":
        context.known_job_names = [job['name'] for job in jobs]
    elif state== "unknown":
        context.unknown_job_names = [job['name'] for job in jobs]

@when('I launch "{num_jobs}" non paasta jobs')
def launch_non_paasta_jobs(context, num_jobs):
    client = context.chronos_client
    jobs = [{
        'async': False,
        'command': 'echo 1',
        'epsilon': 'PT15M',
        'name': 'foobar%d' % job,
        'owner': 'rogue',
        'disabled': True,
        'schedule': 'R/2014-01-01T00:00:00Z/PT60M',
    } for job in range(0, int(num_jobs))]
    context.non_paasta_jobs = [job['name'] for job in jobs]
    for job in jobs:
        try:
            client.add(job)
        except Exception:
            print 'Error creating test job: %s' % json.dumps(job)
            raise


@then('cleanup_chronos_jobs exits with return code "{expected_return_code}" and the correct output')
def check_cleanup_chronos_jobs_output(context, expected_return_code):
    print context.soa_dir
    cmd = '../paasta_tools/cleanup_chronos_jobs.py -d %s' % context.soa_dir
    print 'command >>>'
    print cmd
    (exit_code, output) = _run(cmd)
    print context.unknown_job_names
    print 'Got exitcode %s with output:\n%s' % (exit_code, output)

    assert exit_code == int(expected_return_code)
    assert "Successfully Removed Tasks (if any were running) for:" in output
    assert "Successfully Removed Jobs:" in output
    for job in context.unknown_job_names:
        assert '  %s' % job in output


@then('the non chronos jobs are still in the job list')
def non_paasta_jobs(context):
    jobs = context.chronos_client.list()
    running_job_names = [job['name'] for job in jobs]
    assert all([job_name in running_job_names for job_name in context.non_paasta_jobs])

@then('the "{state}" chronos jobs are not in the job list')
def not_in_job_list(context, state):
    jobs = context.chronos_client.list()
    if state == "known":
        state_list = context.known_job_names
    elif state == "unknown":
        state_list = context.unknown_job_names
    assert_no_job_names_in_list(state_list, jobs)

@then('the "{state}" chronos jobs are in the job list')
def all_in_job_list(context, state):
    jobs = context.chronos_client.list()
    if state == "known":
        state_list = context.known_job_names
    elif state == "unknown":
        state_list = context.unknown_job_names
    assert_all_job_names_in_list(state_list, jobs)


def assert_no_job_names_in_list(names, jobs):
    running_job_names = [job['name'] for job in jobs]
    assert all([job_name not in running_job_names for job_name in names])

def assert_all_job_names_in_list(names, jobs):
    running_job_names = [job['name'] for job in jobs]
    assert all([job_name in running_job_names for job_name in names])
