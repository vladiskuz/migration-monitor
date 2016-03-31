from setuptools import setup, find_packages

setup(
    name="migration-monitor",
    version="0.1",
    packages=find_packages(),
    install_requires=[#'libvirt-python==1.3.2',
                      'influxdb>=2.12.0',
                      'daemonize>=2.4.4',
                      'python-dateutil'],
    entry_points={
        'console_scripts': [
            'migrationmonitor = migrationmonitor.main:main',
        ],
    },
)
