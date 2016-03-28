# Ansible playbooks for starting/stopping telegraf and live migration monitoring

## Start

Run:

	$ ansible-playbook start.yml -i hosts --extra-vars '{"lm_run":"1","lm_scenario":"foo"}'


## Stop

Run:

	$ ansible-playbook stop.yml -i hosts --extra-vars '{"lm_run":"1","lm_scenario":"foo"}'

