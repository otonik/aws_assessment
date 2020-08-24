Name: Zaid Naji
Infra provisioning assessment (Ec2 deployment)
current AWS region: us-east-2
ami_id: ami-0d8f6eb4f641ef691

- Deployment for infra is done through boto3 (as Cloudformation/terraform/IaaC were not allowed in the requirements)
- demo deploys 2 backend nodejs express servers and 1 nginx load balancer
- Requires atleast Python 3.6
- Install dependencies
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

