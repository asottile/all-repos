import multiprocessing


def add_config_arg(parser):
    parser.add_argument('-C', '--config-filename', default='all-repos.json')


def jobs_type(s):
    jobs = int(s)
    if jobs <= 0:
        return multiprocessing.cpu_count()
    else:
        return jobs


def add_jobs_arg(parser):
    parser.add_argument('-j', '--jobs', type=jobs_type, default=8)
