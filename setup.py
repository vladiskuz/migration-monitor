from setuptools import setup, find_packages

setup(
    name="migration-monitor",
    version="0.1",
    packages=find_packages(),
    install_requires=['pyvmomi>=6.0.0.2016.6',
                      'colorlog>=2.7.0',
                      'influxdb>=2.12.0',
                      # 'libvirt-python>=1.3.2',
                      'daemonize>=2.4.4'],

    entry_points={
        'console_scripts': [
            'migrationmonitor = migrationmonitor.main:main',
        ],
    },
)
