# Ansible playbooks for starting/stopping telegraf and live migration monitoring

## Start

Run:

	$ ansible-playbook start.yml -i hosts --extra-vars '{"lm_run":"1","lm_scenario":"foo"}'


## Stop

Run:

	$ ansible-playbook stop.yml -i hosts


## Update nova flags and restart n-cpu

Run:

	$ ansible-playbook nova_flags.yml -i hosts --extra-vars '{"nova_compress":"yes","nova_autoconverge":"no"}'
