import base64
import os
import unittest

from kubernetes.client.models.v1_job import V1Job
from ruamel import yaml

from pycalrissian.context import CalrissianContext
from pycalrissian.job import CalrissianJob

os.environ["KUBECONFIG"] = "~/.kube/kubeconfig-t2-dev.yaml"


class TestCalrissianJob(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace = "job-namespace"

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
            namespace=cls.namespace,
            storage_class="openebs-kernel-nfs-scw",  # "microk8s-hostpath",
            volume_size="10G",
            image_pull_secrets=secret_config,
        )

        session.initialise()

        cls.session = session

    @classmethod
    def tearDown(cls):
        cls.session.dispose()

    @unittest.skipIf(os.getenv("CI_TEST_SKIP") == "1", "Test is skipped via env variable")
    def test_job(self):
        # TODO check why this fails with namespace is being terminated
        document = "tests/simple.cwl"
        with open(document) as doc_handle:
            yaml_obj = yaml.YAML()
            cwl = yaml_obj.load(doc_handle)

        params = {"message": "hello world!"}

        pod_env_vars = {"C": "1", "B": "2"}

        job = CalrissianJob(
            cwl=cwl,
            params=params,
            runtime_context=self.session,
            pod_env_vars=pod_env_vars,
            # pod_node_selector={
            #     "k8s.scaleway.com/pool-name": "processing-node-pool-dev"
            # },
            debug=True,
            max_cores=2,
            max_ram="4G",
            keep_pods=True,
        )

        job.to_yaml("job.yml")
        self.assertIsInstance(job.to_k8s_job(), V1Job)

    def test_calrissian_image(self):

        os.environ["CALRISSIAN_IMAGE"] = "terradue/calrissian:latest"

        document = "tests/simple.cwl"

        with open(document) as doc_handle:
            yaml_obj = yaml.YAML()
            cwl = yaml_obj.load(doc_handle)

        params = {"message": "hello world!"}

        job = CalrissianJob(
            cwl=cwl,
            params=params,
            runtime_context=self.session,
            pod_env_vars={},
            pod_node_selector={},
            debug=True,
            max_cores=2,
            max_ram="4G",
            keep_pods=True,
        )

        self.assertEqual(
            job.to_k8s_job().spec.template.spec.containers[0].image,
            os.environ["CALRISSIAN_IMAGE"],
        )
