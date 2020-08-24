Name: Zaid Naji <br />
Infra provisioning assessment (EC2 deployment) <br />
AWS region: us-east-2 <br />
AMI id: ami-0d8f6eb4f641ef691 <br />

- Deployment for infra is done through boto3 (as Cloudformation/terraform/IaaC were not allowed in the requirements)
- demo deploys 2 backend nodejs express servers and 1 nginx load balancer
- Requires atleast Python 3.6

#
- <b>Install dependencies
```bash
pip install -r requirements.txt
```
- To run the demo
```bash
python ./createWebInfra.py
```

- To tear down the infra
```bash
python ./createWebInfra.py --teardown
```