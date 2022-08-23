import base64
import os
import unittest

from kubernetes.client.models.v1_job import V1Job
from ruamel import yaml

from pycalrissian.context import CalrissianContext
from pycalrissian.job import CalrissianJob

os.environ["KUBECONFIG"] = "/home/mambauser/.kube/kubeconfig-t2-dev.yaml"


class TestCalrissianJob(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace = "job-namespace"

    def test_job(self):

        username = "pippo"
        password = "pippo"
        email = "john.doe@me.com"
        registry = "1ui32139.gra7.container-registry.ovh.net"

        auth = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode(
            "utf-8"
        )

        secret_config = {
            "auths": {
                registry: {
                    "username": username,
                    "password": password,
                    "email": email,
                    "auth": auth,
                }
            }
        }

        session = CalrissianContext(
            namespace=self.namespace,
            storage_class="longhorn",  # "microk8s-hostpath",
            volume_size="10G",
            image_pull_secrets=secret_config,
        )

        session.initialise()

        # with open("tests/simple.cwl", "r") as stream:

        #     cwl = yaml.safe_load(stream)
        document = "tests/simple.cwl"
        with open(document) as doc_handle:
            cwl = yaml.main.round_trip_load(doc_handle, preserve_quotes=True)

        params = {"message": "hello world!"}

        pod_env_vars = {"C": "1", "B": "2"}

        job = CalrissianJob(
            cwl=cwl,
            params=params,
            runtime_context=session,
            pod_env_vars=pod_env_vars,
            pod_node_selector={"key": "value"},
            debug=True,
            max_cores=2,
            max_ram="4G",
            keep_pods=True,
        )

        job.to_yaml("job.yml")
        self.assertIsInstance(job.to_k8s_job(), V1Job)
