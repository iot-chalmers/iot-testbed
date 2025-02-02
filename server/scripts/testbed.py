#!/usr/bin/env python3

# Simon Duquennoy (simonduq@sics.se)

import os
import shutil
import sys
import getopt
import getpass
import time
import signal
import pwd
import grp
import subprocess
import re
import datetime
import pytz
import multiprocessing
from psshlib import *

curr_job = None
curr_job_owner = None
curr_job_date = None
job_dir = None
hosts_path = None

# value of the command line parameters
name = None
platform = None
duration = None
copy_from = None
job_id = None
hosts = None
do_start = False
do_force = False
do_no_download = False
do_start_next = False
metadata = None
post_processing = None
is_nested = False
force_reboot = False
forward_serial = False

MAX_START_ATTEMPTS = 3
TESTBED_PATH = "/usr/testbed"
TESTBED_SCRIPTS_PATH = os.path.join(TESTBED_PATH, "scripts")
LOCK_PATH = os.path.join(TESTBED_PATH, "lock")
HISTORY_FILE_PATH = os.path.join(TESTBED_PATH, "history")
CURR_JOB_PATH = os.path.join(TESTBED_PATH, "curr_job")
CURR_JOB_OWNER_PATH = os.path.join(TESTBED_PATH, "curr_job_owner")
CUR_USER_HOME = os.path.expanduser("~")
USER = getpass.getuser()
next_job_path = os.path.join(TESTBED_PATH, "next_job")
next_job_path_user = os.path.join(TESTBED_PATH, "next_job_%s" % (USER))
user_queue_file = os.path.join(TESTBED_PATH, "next_user")
testbed_info_file = os.path.join(TESTBED_PATH, "testbed_info")
GENERAL_JOB_DIR = os.path.join(TESTBED_PATH, "jobs")


def log(msg, toHistory=True, toConsole=True):
    """Log messages to console and to history file"""
    if toHistory:
        file_append(HISTORY_FILE_PATH,
                    msg + "\n")
    if toConsole:
        print(msg)


def get_user_home(user):
    """Get the home directory for a user"""
    return os.path.join("/home/%s" % user)


def get_next_job_path_user(user):
    """@Deprecated: Will be removed later"""
    return os.path.join(TESTBED_PATH, "next_job_%s" % (user))


def lock_is_taken():
    """Check, if the lock is currently taken"""
    return os.path.exists(LOCK_PATH)


def lock_aquire():
    """Get the lock"""
    if not is_nested:
        try:
            open(LOCK_PATH, 'a').close()
        except Exception as e:
            print("Could not aquire lock!")
            print(e)
            sys.exit(1)


def lock_release():
    if not is_nested and lock_is_taken():
        try:
            os.remove(LOCK_PATH)
        except Exception as e:
            print("Could not release lock!")
            print(e)
            sys.exit(1)


def do_quit(status):
    lock_release()
    sys.exit(status)


def timestamp():
    return datetime.datetime.now(tz=pytz.timezone('Europe/Stockholm')).isoformat()


def file_set_group_permission(path):
    if os.path.exists(path):
        try:
            gid = grp.getgrnam("testbed").gr_gid
            uid = pwd.getpwnam(USER).pw_uid
            os.chown(path=path, uid=uid, gid=gid)
            # os.chmod(path, 0o660)
        except Exception as e:
            print("Failed to set permissions for file '%s'" % path)
            print(e)
            do_quit(1)


def file_set_permissions(path):
    # whenever writing to a file in TESTBED_PATH for the first time, set group as "testbed"
    if path.startswith(TESTBED_PATH) and not os.path.exists(path):
        try:
            file = open(path, "w")
            file.close()
            uid = pwd.getpwnam(USER).pw_uid
            gid = grp.getgrnam("testbed").gr_gid
            os.chown(path, uid, gid)
            os.chmod(path, 0o660)
        except Exception as e:
            print("Failed to set permissions for file '%s'" % path)
            print(e)
            do_quit(1)


def file_read(path):
    if os.path.exists(path):
        try:
            return open(path, "r").read()
        except Exception as e:
            print("Failed to read contents of file '%s'" % path)
            print(e)
            do_quit(1)
    else:
        return None


def file_write(path, str):
    file_set_permissions(path)
    try:
        file = open(path, "w")
        file.write(str)
    except Exception as e:
        print("Failed to write to file '%s'" % path)
        print(e)
        do_quit(1)


def file_prepend(path, string):
    content = file_read(path)
    if content or content == "":
        content = string + content
        file_write(path, content)


def file_append(path, str):
    file_set_permissions(path)
    try:
        file = open(path, "a")
        file.write(str)
    except Exception as e:
        print("Failed to append content to file '%s'" % path)
        print(e)
        do_quit(1)


def getNextJobUser():
    """Get next user name from user queue"""
    content = file_read(user_queue_file)
    if content:
        names = content.rstrip().split("\n")
        user = names[0]
        if user:
            names = names[1:]
        content = ""
        for name in names:
            content = content + name + "\n"
        file_write(user_queue_file, content)
        return user
    return None


def queueNextUser(user):
    """Insert a new user into the queue"""
    file_append(user_queue_file, "%s\n" % user)


# checks is any element of aset is in seq


def contains_any(seq, aset):
    for c in seq:
        if c in aset:
            return True
    return False

# get job directory from id


def get_job_directory(user, job_id):
    jobs_dir = os.path.join(GENERAL_JOB_DIR, user)
    if os.path.isdir(jobs_dir):
        for f in os.listdir(jobs_dir):
            if f.startswith("%d_" % (job_id)):
                return os.path.join(jobs_dir, f)
    return None

# load all variables related to the currently active job


def load_curr_job_variables(need_curr_job, need_no_curr_job):
    """Load current job variables like job-id, job-owner and job-date."""
    global curr_job, curr_job_owner, curr_job_date
    if not os.path.exists(CURR_JOB_PATH) or not os.path.exists(CURR_JOB_OWNER_PATH):
        curr_job = None
        curr_job_owner = None
    else:
        try:
            curr_job = int(file_read(CURR_JOB_PATH))
            curr_job_owner = file_read(CURR_JOB_OWNER_PATH)
        except Exception:
            print(
                "Error loading job variables!\nContent of '%s' is no valid number" % CURR_JOB_PATH)
            do_quit(1)
        curr_job_date = os.stat(CURR_JOB_PATH).st_ctime
    if need_curr_job and not curr_job and curr_job != 0:
        print("There is no active job!")
        do_quit(1)

# load all variables related to a given job


def load_job_variables(user, job_id):
    """Load job-directory, platform, host-path and job-duration for given job."""
    global job_dir, platform, hosts_path, duration
    # check if the job exists
    job_dir = get_job_directory(user, job_id)
    if job_dir == None:
        print("Job %u not found! %s" % (job_id, user))
        do_quit(1)
    # read what the platform for this job is
    platform = file_read(os.path.join(job_dir, "platform")).rstrip()
    # get path to the hosts file (list of PI nodes involved)
    hosts_path = os.path.join(job_dir, "hosts")
    # get path to the duration file
    # duration_path = os.path.join(job_dir, "duration")
    duration = file_read(os.path.join(job_dir, "duration"))
    if duration != None:
        duration = int(duration)


def create(name, platform, hosts, copy_from, do_start, duration, metadata, post_processing):
    """Create a new job with given name, platform, hosts, source-directory to copy from. Start it, if 'do_start' is true, set a max duration,
       set metadata and set a post-processing script.
    """
    # if do_start is set, first check that there is no job active
    if do_start:
        load_curr_job_variables(False, True)
    # if name is not set, use either the copy-from dir name or "noname"
    if not name:
        if copy_from:
            name = os.path.basename(copy_from).split('.')[0]
        else:
            name = "noname"
    # check validity of name
    if contains_any(name, [' ', '.', ',', '/']):
        print("Name %s is not valid!" % (name))
        do_quit(1)

    # if host is not set, take it from copy-from or use the default all-hosts file
    if not hosts:
        if copy_from and os.path.exists(os.path.join(copy_from, "hosts")):
            hosts = os.path.join(copy_from, "hosts")
        else:
            hosts = os.path.join(TESTBED_SCRIPTS_PATH, "all-hosts")
    # check if host file exists
    if not os.path.isfile(hosts):
        print("Host file %s not found!" % (hosts))
        do_quit(1)

    # if platform is not set, take it from copy-from or use "noplatform"
    if not platform:
        if copy_from and os.path.isfile(os.path.join(copy_from, "platform")):
            platform = file_read(os.path.join(copy_from, "platform"))
        else:
            platform = "noplatform"
    # check if the platform exists
    platform_path = os.path.join(TESTBED_SCRIPTS_PATH, platform)
    if not os.path.isdir(platform_path):
        print("Platform %s not found!" % (platform))
        do_quit(1)

    # if duration is not set, take it from copy-from
    if duration == None:
        if copy_from and os.path.isfile(os.path.join(copy_from, "duration")):
            duration = file_read(os.path.join(copy_from, "duration"))

    if os.path.exists(next_job_path):
        job_id = int(file_read(next_job_path))
    else:
        job_id = 0
        file_write(next_job_path, "%u\n" % (job_id))

    # check if job id is already used
    job_dir = get_job_directory(USER, job_id)
    if job_dir:
        print("Job %d already exists! Delete %s before creating a new job." %
              (job_id, job_dir))
        do_quit(1)

    # create user job directory
    job_dir = os.path.join(GENERAL_JOB_DIR, USER, "%u_%s" %
                           (job_id, name))
    # initialize job directory from copy_from command line parameter
    if copy_from:
        if os.path.isdir(copy_from):
            # copy full directory
            try:
                shutil.copytree(copy_from, job_dir)
            except Exception as e:
                print("Could not copy directory %s to %s" %
                      (copy_from, job_dir))
                print(e)
                do_quit(1)
        else:
            # copy single file
            copy_to = os.path.join(job_dir, os.path.basename(copy_from))
            try:
                os.makedirs(job_dir)
                shutil.copyfile(copy_from, copy_to)
            except Exception as e:
                print("Could not copy file %s to %s" % (copy_from, copy_to))
                print(e)
                do_quit(1)
    else:
        try:
            os.makedirs(job_dir)
        except OSError as e:
            print("Failed to create directory %s" % job_dir)
            print(e)
            do_quit(1)
    # set file permissions for directories
    file_set_group_permission(job_dir)
    file_set_group_permission(os.path.join(GENERAL_JOB_DIR, USER))
    # copy metadata file, if any
    if metadata:
        dest = os.path.join(
            job_dir, os.path.basename(metadata))
        try:
            shutil.copyfile(metadata, dest)
        except Exception as e:
            print("Failed to copy metadata to %s" % dest)
            print(e)
            do_quit(1)
    # copy post-processing script, if any
    if post_processing:
        post_processing_path = os.path.join(job_dir, "post_processing.sh")
        try:
            shutil.copyfile(post_processing, post_processing_path)
            os.chmod(post_processing_path, 740)
        except Exception as e:
            print("Failed to copy post-processing script %s to %s" %
                  (post_processing, post_processing_path))
            print(e)
            do_quit(1)
    # create host file in job directory
    try:
        new_host_file = os.path.join(job_dir, "hosts")
        shutil.copyfile(hosts, new_host_file)
        file_set_group_permission(new_host_file)
    except OSError as e:
        print("Failed to copy host file %s to %s" %
              (hosts, os.path.join(job_dir, "hosts")))
        print(e)
        do_quit(1)
    # create platform file in job directory
    file_write(os.path.join(job_dir, "platform"), platform + "\n")
    if duration != None:
        # create duration file in job directory
        file_write(os.path.join(job_dir, "duration"), duration + "\n")
    # write creation timestamp
    ts = timestamp()
    file_write(os.path.join(job_dir, ".created"), ts + "\n")  # write history
    history_message = "%s: %s created job %u, platform:%s, hosts:%s, copy-from:%s, directory:%s" % (
        ts, USER, job_id, platform, hosts, copy_from, job_dir)
    log(history_message)
    file_write(next_job_path, "%u\n" % (job_id+1))
    if do_start:
        start(job_id)


def status():
    """Get the status of the testbed. Including information about running job."""
    load_curr_job_variables(False, False)
    if curr_job == None:
        print("No job currently active")
    else:
        curr_job_date_str = datetime.datetime.fromtimestamp(
            curr_job_date).strftime('%Y-%m-%d %H:%M:%S')
        print("Currently active job: %u, owned by %s, started %s" %
              (curr_job, curr_job_owner, curr_job_date_str))
    try:
        process = subprocess.Popen(['date', '+%s%N'], stdout=subprocess.PIPE)
        out, _err = process.communicate()
        curr_date = out.rstrip()
        # check current date on all nodes
        if pssh(os.path.join(TESTBED_SCRIPTS_PATH, "all-hosts"), "check-date.sh %s" % (curr_date.decode("UTF-8")), "Testing connectivity with all nodes", merge_path=True, inline=True) != 0:
            do_quit(1)
    except Exception as e:
        print("Failed to check for dates on nodes")
        print(e)
        do_quit(1)


def list():
    """List all jobs."""
    all_jobs = {}
    jobs_dir = os.path.join(GENERAL_JOB_DIR, USER)
    if os.path.isdir(jobs_dir):
        for f in os.listdir(jobs_dir):
            match = re.search(r'(\d+)_(.*)+', f)
            if match:
                try:
                    job_id = int(match.group(1))
                except Exception:
                    print(
                        "Files in '%s' are not named properly to retrieve the job number." % jobs_dir)
                    do_quit(1)
                job_dir = os.path.join(jobs_dir, f)
                platform = file_read(os.path.join(job_dir, "platform"))
                duration = file_read(os.path.join(job_dir, "duration"))
                if not duration:
                    duration = 999999
                else:
                    try:
                        duration = int(duration)
                    except Exception:
                        duration = 999999
                created = file_read(os.path.join(job_dir, ".created"))
                if not created:
                    created = "--"
                else:
                    created = created.split('.')[0]
                started = file_read(os.path.join(job_dir, ".started"))
                if not started:
                    started = "--"
                else:
                    started = started.split('.')[0]
                stopped = file_read(os.path.join(job_dir, ".stopped"))
                if not stopped:
                    stopped = "--"
                else:
                    stopped = stopped.split('.')[0]
                logs_path = os.path.join(job_dir, "logs")
                if os.path.isdir(logs_path):
                    n_log_files = sum(1 for _ in filter(lambda x: x.startswith("raspi"), os.listdir(logs_path)))
                else:
                    n_log_files = 0
                all_jobs[job_id] = {"dir": f, "platform": platform, "duration": duration,
                                    "created": created, "started": started, "stopped": stopped,
                                    "n_log_files": n_log_files}
    for job_id in sorted(all_jobs.keys()):
        print("{:6d} {:36s} {:12s} duration: {:6d} min, created: {:19s}, started: {:19s}, stopped: {:19s}, logs: {:2d} nodes".format(
            job_id, all_jobs[job_id]['dir'],
            all_jobs[job_id]['platform'], all_jobs[job_id]['duration'], all_jobs[job_id]['created'],
            all_jobs[job_id]['started'], all_jobs[job_id]['stopped'],
            all_jobs[job_id]['n_log_files']
        ))


def get_next_job_id():
    """Get the next job id, depending on the fact, whether there is a user in the queue or not"""
    global next_user
    next_user = getNextJobUser()
    actual_user = next_user if next_user else USER
    jobs_dir = os.path.join(GENERAL_JOB_DIR, actual_user)
    if os.path.isdir(jobs_dir):
        for f in sorted(os.listdir(jobs_dir)):
            match = re.search(r'(\d+)_(.*)+', f)
            if match:
                try:
                    job_id = int(match.group(1))
                except Exception:
                    print(
                        "Files in '%s' are not named properly to retrieve the job number." % jobs_dir)
                    do_quit(1)
                job_dir = os.path.join(jobs_dir, f)
                if not os.path.isfile(os.path.join(job_dir, ".started")):
                    return job_id
    return None


def start(job_id):
    """Start a job with a given job id"""
    job_id = get_next_job_id()

    # get the next job id and skip entries of users with no pending (unstarted) jobs
    while job_id == None and next_user != None:
        job_id = get_next_job_id()

    if job_id == None:
        print("There is no next job!")
        return

    load_curr_job_variables(False, True)
    # If there is no current job, load the job variables of the next job for the issuing user
    user_to_load_variables_for = next_user if next_user else USER
    if curr_job == None:
        load_job_variables(user_to_load_variables_for, job_id)
    if job_dir and os.path.exists(os.path.join(job_dir, ".started")):
        print("Job %d was started before!" % (job_id))
        do_quit(1)
    # Add jobs to a queue
    if curr_job != None:
        # User tries to start a job, while one job is already running
        if next_user:
            file_prepend(user_queue_file, "%s\n" % next_user)
        queueNextUser(USER)
        ts = timestamp()
        log("%s: %s queued a job." % (ts, USER))
        do_quit(0)
    started = False
    attempt = 1
    while not started and attempt <= MAX_START_ATTEMPTS:
        print("Attempt #%u to start job %u" % (attempt, job_id))
        # on all PI nodes: prepare
        if pssh(hosts_path, "prepare.sh %s" % (os.path.basename(job_dir)), "Preparing the PI nodes", merge_path=True) == 0:
            # run platform start script
            start_script_path = os.path.join(
                TESTBED_SCRIPTS_PATH, platform, "start.py")
            if os.path.exists(start_script_path) and subprocess.call([start_script_path, job_dir, "forward" if forward_serial else ""]) == 0:
                started = True
            else:
                print("Platform start script %s failed" % (start_script_path))
        else:
            print("Platform prepare script %s failed" %
                  (os.path.basename(job_dir)))
        if not started:
            print("Platform prepare or start script failed, cleanup the PI nodes!")
            # on all PI nodes: cleanup
            stop_script_path = os.path.join(
                TESTBED_SCRIPTS_PATH, platform, "stop.py")
            if os.path.exists(stop_script_path):
                subprocess.call([stop_script_path, job_dir])
            pssh(hosts_path, "cleanup.sh %s" % (os.path.basename(job_dir)),
                 "Cleaning up the PI nodes", merge_path=True)
            reboot()
            attempt += 1
    if not started:
        print("Platform start script %s failed after %u attempts." %
              (start_script_path, attempt))
        do_quit(1)
    # update curr_job file to know that this job is active
    file_write(CURR_JOB_PATH, "%u\n" % (job_id))
    file_write(CURR_JOB_OWNER_PATH, "%s" % user_to_load_variables_for)
    # write start timestamp
    ts = timestamp()
    file_write(os.path.join(job_dir, ".started"), ts + "\n")
    # write history
    history_message = "%s: %s started job %u, platform %s, directory %s" % (
        ts, user_to_load_variables_for, job_id, platform, job_dir)
    log(history_message, toConsole=False)
    # schedule end of job if a duration is set
    if duration != None:
        print("Scheduling end of job in %u min" % (duration))
        # schedule in duration + 1 to account for the currently begun minute
        py_testbed_script_path = os.path.join(
            TESTBED_SCRIPTS_PATH, "testbed.py")
        os.system("echo '%s stop --force --start-next'  | at -q t now + %u min" %
                  (py_testbed_script_path, duration + 1))
    print(history_message)


def rsync(src, dst):
    print("rsync -avz %s %s" % (src, dst))
    return subprocess.call(["rsync", "-az", src, dst])


def download():
    """Download the logs of the current job."""
    load_curr_job_variables(True, False)
    # job_id = curr_job
    load_job_variables(curr_job_owner, curr_job)
    # download log file from all PI nodes
    remote_logs_dir = os.path.join(
        "/home/user/logs", os.path.basename(job_dir))
    logs_dir = os.path.join(job_dir, "logs")
    # pslurp(hosts_path, remote_logs_dir, logs_dir, "Downloading logs from the PI nodes")
    hosts = filter(lambda x: x != '', map(
        lambda x: x.rstrip(), open(hosts_path, 'r').readlines()))
    # rsync log dir from all PI node
    rsync_processes = []
    print("Synchronizing logs from all hosts")
    for host in hosts:
        host_log_path = os.path.join(logs_dir, host)
        if not os.path.exists(host_log_path):
            try:
                os.makedirs(host_log_path)
            except Exception as e:
                print("Failed to create directory '%s'" % host_log_path)
                print(e)
                do_quit(1)
        file_set_group_permission(host_log_path)
        curr_remote_logs_uri = "user@%s:" % (host) + \
            os.path.join(remote_logs_dir, "*")
        p = multiprocessing.Process(target=rsync, args=(
            curr_remote_logs_uri, host_log_path,))
        p.start()
        rsync_processes.append(p)
    for p in rsync_processes:
        p.join()
    # Set permissions for the logs dir
    file_set_group_permission(logs_dir)
    # run platform download script
    download_script_path = os.path.join(
        TESTBED_SCRIPTS_PATH, platform, "download.py")
    if os.path.exists(download_script_path) and subprocess.call([download_script_path, job_dir]) != 0:
        print("Platform download script %s failed!" % (download_script_path))
        # do_quit(1)
        return 1
    return 0


def stop(do_force):
    """Stop the current job on all Pis"""
    load_curr_job_variables(True, False)
    job_id = curr_job
    load_job_variables(curr_job_owner, job_id)
    # cleanup the PI nodes
    # run platform stop script
    stop_script_path = os.path.join(TESTBED_SCRIPTS_PATH, platform, "stop.py")
    if os.path.exists(stop_script_path) and subprocess.call([stop_script_path, job_dir]) != 0:
        print("Platform stop script %s failed!" % (stop_script_path))
        if not do_force:
            do_quit(1)
    if not do_no_download:
        # download logs before stopping
        download()
    # on all PI nodes: cleanup
    if pssh(hosts_path, "cleanup.sh %s" % (os.path.basename(job_dir)), "Cleaning up the PI nodes", merge_path=True) != 0:
        print("Rebooting the nodes")
        reboot()  # something went probably wrong with serialdump, reboot the nodes
        if not do_force:
            do_quit(1)
    # remove current job-related files
    try:
        os.remove(CURR_JOB_PATH)
        os.remove(CURR_JOB_OWNER_PATH)
    except Exception:
        print("Failed to remove '%s' or '%s'" %
              (CURR_JOB_PATH, CURR_JOB_OWNER_PATH))
    # write stop timestamp
    ts = timestamp()
    file_write(os.path.join(job_dir, ".stopped"), ts + "\n")
    # write history
    history_message = "%s: %s stopped job %u, platform %s, directory %s" % (
        ts, curr_job_owner, job_id, platform, job_dir)
    log(history_message, toConsole=False)
    # kill at jobs (jobs scheduled to stop in the future)
    print("Killing pending at jobs")
    os.system("for i in `atq -q t | awk '{print $1}'`;do atrm $i;done")
    # start next job if requested
    if do_start_next:
        print("Starting next job")
        start(None)
    # run post-processing script
    post_processing_path = os.path.join(job_dir, "post_processing.sh")
    if os.path.exists(post_processing_path):
        command = "%s %u" % (post_processing_path, job_id)
        print("Running command: '%s'" % (command))
        os.system(command)
    print(history_message)


def reboot():
    """Reboot all the Pis"""
    if force_reboot:
        d = 60
        load_curr_job_variables(False, True)
        # reboot all PI nodes
        if pssh(os.path.join(TESTBED_SCRIPTS_PATH, "all-hosts"), "sudo reboot", "Rebooting the PI nodes", merge_path=False) != 0:
            print("Failed to restart the PI nodes")
            do_quit(1)
        # write history
        ts = timestamp()
        history_message = "%s: %s rebooted the PI nodes. Waiting %u s." % (
            ts, USER, d)
        log(history_message)
        time.sleep(d)  # wait 60s to give time for reboot
    else:
        ts = timestamp()
        history_message = "%s: %s has disabled reboot, but there was a problem beforehand" % (
            ts, USER)
        log(history_message)


def usage():
    print("Usage: $testbed.py command [--parameter value]")
    print()
    print("Commands:")
    print("create             'create a job for future use'")
    print("start              'start a job'")
    print("download           'download the current job's logs'")
    print("stop               'stop the current job and download its logs'")
    print()
    print("status             'show status of the currently active job'")
    print("list               'list all your jobs'")
    print()
    print("reboot             'reboot the PI nodes (for maintenance purposes -- use with care)'")
    print()
    print("Usage of create:")
    print(
        " $ testbed.py create [--copy-from PATH] [--name NAME] [--platform PLATFORM] [--hosts HOSTS] [--start]")
    print("--copy-from        'initialize job directory with content from PATH (if PATH is a directory) or with file PATH (otherwise)'")
    print("--name             'set the job name (no spaces)'")
    print("--platform         'set a platform for the job (must be a folder in %s)'" %
          (TESTBED_SCRIPTS_PATH))
    print("--duration         'job duration in minutes (optional). If set, the next job will start automatically after the end of the current.'")
    print("--hosts            'set the hostfile containing all PI host involved in the job'")
    print("--start            'start the job immediately after creating it'")
    print("--metadata         'copy any metadata file to job directory'")
    print("--post-processing  'call a given post-processing script at the end of the run'")
    print("--nested           'set this if calling from a script that already took the lock'")
    print("--with-reboot      'reboot the raspberry PIs if the job creation fails'")
    print("--forward-serial   'Forwards the serial line data into a TCP socket (tcp://raspi:50000)'")
    print()
    print("Usage of start:")
    print(" $ testbed.py start [--job-id ID]")
    print("--job-id           'the unique job id (obtained at creation). If not set, start next job.'")
    print()
    print("Usage of stop:")
    print(" $ testbed.py stop [--force] [--no-download]")
    print("--force            'stop the job even if uninstall scripts fail'")
    print("--no-download      'do not download the logs before stopping'")
    print("--start-next       'start next job after stopping the current'")
    print()
    print("Usage of status, list, download, stop, reboot:")
    print("These commands use no parameter.")
    print()
    print("Examples:")
    print(" $ testbed.py create --copy-from /usr/testbed/examples/jn516x-hello-world --start     'create and start a JN516x hello-world job'")
    print(" $ testbed.py stop                                                                    'stop the job and download the logs'")
    print()


def signal_handler(sig, frame):
    """Catpure CTRL + C to free lock if taken"""
    print("Exiting gracefully!")
    do_quit(1)


if __name__ == "__main__":
    try:
        # Check, if enough arguments are given
        if len(sys.argv) < 2:
            usage()
            sys.exit(1)

        signal.signal(signal.SIGINT, signal_handler)

        # Try to fettch arguments
        try:
            opts, args = getopt.getopt(sys.argv[2:], "", ["name=", "platform=", "hosts=", "copy-from=", "duration=", "job-id=", "start",
                                                          "force", "no-download", "start-next", "metadata=", "post-processing=", "nested", "with-reboot", "forward-serial"])
        except getopt.GetoptError as e:
            print(e)
            usage()
            sys.exit(1)

        command = sys.argv[1]

        for opt, value in opts:
            if opt == "--name":
                name = value
            elif opt == "--platform":
                platform = value
            elif opt == "--hosts":
                hosts = os.path.normpath(value)
            elif opt == "--copy-from":
                copy_from = os.path.normpath(value)
            elif opt == "--job-id":
                try:
                    job_id = int(value)
                except Exception as e:
                    print("Error: --job-id expects an number as argument")
                    sys.exit(1)
            elif opt == "--duration":
                duration = value
            elif opt == "--start":
                do_start = True
            elif opt == "--force":
                do_force = True
            elif opt == "--no-download":
                do_no_download = True
            elif opt == "--start-next":
                do_start_next = True
            elif opt == '--post-processing':
                post_processing = value
            elif opt == "--metadata":
                metadata = value
            elif opt == "--nested":
                is_nested = True
            elif opt == "--with-reboot":
                force_reboot = True
            elif opt == "--forward-serial":
                forward_serial = True

        if not is_nested and lock_is_taken():
            print("Lock is taken. Try a gain in a few seconds/minutes.")
            sys.exit(1)
        else:
            lock_aquire()

        if command == "create":
            create(name, platform, hosts, copy_from, do_start,
                   duration, metadata, post_processing)
        elif command == "status":
            status()
        elif command == "list":
            list()
        elif command == "start":
            start(job_id)
        elif command == "download":
            download()
        elif command == "stop":
            stop(do_force)
        elif command == "reboot":
            reboot()
        else:
            usage()
    except Exception as e:
        print(e)
        do_quit(1)

    do_quit(0)
