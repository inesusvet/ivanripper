#!/usr/bin/env python
#-*- encoding: utf-8 -*-
"""
Приложение для вскрытия md5 хэшей.
Функциональные возможности:

    Получение хэшей в кодировке base64.
    Определение кол-ва процессоров на вычислительной системе и
    параллельный запуск соответствующего кол-ва процессов перебора хэшей.
    Определение процессорного времени, затраченного на подбор хэша.
"""

from multiprocessing import Pool
from itertools import product, ifilter, chain

from string import ascii_letters
import hashlib
import time

DEFAULT_CHARSET = ascii_letters


def gen_printable_sequence(limit=10, charset=DEFAULT_CHARSET):
    seq = chain.from_iterable(product(*([charset] * (i + 1)))
                              for i in xrange(limit))
    return (''.join(i) for i in seq)


def get_md5hex(string):
    md5hex = hashlib.md5()
    md5hex.update(string)
    return md5hex.hexdigest()


def rip(variant, md5hex):
    return get_md5hex(variant) == md5hex


def identity(arg):
    return arg


def gen_checks(md5hex, variant_sequence):
    for variant in variant_sequence:
        match = rip(variant, md5hex)
        yield match, variant
        if match:
            break


def get_stat_info(pid):
    with open(r'/proc/%s/stat' % pid, 'r') as statfile:
        return statfile.read().split(' ')


def get_cpu_time(pool):
    return map(lambda p: map(
        float,
        get_stat_info(p.pid)[13:15]
    ), pool._pool)


def main():
    md5_passphrase = get_md5hex(raw_input('passphrase: '))

    pool = Pool(processes=2)

    time1 = time.time()
    pool_cpu_time1 = get_cpu_time(pool)

    # -----------------------------
    #FIXME: WTF? Все выполняется внутри print??!
    print next(ifilter(
        lambda x: x[0],
        pool.imap(
            identity,
            gen_checks(
                md5_passphrase,
                gen_printable_sequence()
            ),
            chunksize=1024 * 4
        )
    ))
    # -----------------------------

    print 'Time spent: %f' % (time.time() - time1)
    time2 = time.time()

    pool_cpu_time2 = get_cpu_time(pool)

    for cpu_time1, cpu_time2 in zip(pool_cpu_time1, pool_cpu_time2):
        cpu_time1 = sum(cpu_time1)
        cpu_time2 = sum(cpu_time2)
        cpu_usage = float(cpu_time2 - cpu_time1) / (time2 - time1)
        print 'Worker cpu usage: %s' % cpu_usage

    pool.close()
    pool.join()

if __name__ == '__main__':
    main()
