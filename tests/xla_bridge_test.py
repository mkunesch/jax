# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import warnings
import time

from absl.testing import absltest
from jax.lib import xla_bridge as xb
from jax.lib import xla_client as xc
from jax import test_util as jtu

mock = absltest.mock


def mock_tpu_client():
  time.sleep(0.03)
  return None

class XlaBridgeTest(absltest.TestCase):

  def test_set_device_assignment_no_partition(self):
    compile_options = xb.get_compile_options(
        num_replicas=4, num_partitions=1, device_assignment=[0, 1, 2, 3])
    expected_device_assignment = ("Computations: 1 Replicas: 4\nComputation 0: "
                                  "0 1 2 3 \n")
    self.assertEqual(compile_options.device_assignment.__repr__(),
                     expected_device_assignment)

  def test_set_device_assignment_with_partition(self):
    compile_options = xb.get_compile_options(
        num_replicas=2, num_partitions=2, device_assignment=[[0, 1], [2, 3]])
    expected_device_assignment = ("Computations: 2 Replicas: 2\nComputation 0: "
                                  "0 2 \nComputation 1: 1 3 \n")
    self.assertEqual(compile_options.device_assignment.__repr__(),
                     expected_device_assignment)

  def test_parameter_replication_default(self):
    c = xb.make_computation_builder("test")
    _ = xb.parameter(c, 0, xc.Shape.array_shape(xc.PrimitiveType.F32, ()))
    built_c = c.Build()
    assert "replication" not in built_c.as_hlo_text()

  def test_parameter_replication(self):
    c = xb.make_computation_builder("test")
    _ = xb.parameter(c, 0, xc.Shape.array_shape(xc.PrimitiveType.F32, ()), "", False)
    built_c = c.Build()
    assert "parameter_replication={false}" in built_c.as_hlo_text()

  def test_local_devices(self):
    self.assertNotEmpty(xb.local_devices())
    with self.assertRaisesRegex(ValueError, "Unknown process_index 100"):
      xb.local_devices(100)
    with self.assertRaisesRegex(RuntimeError, "Unknown backend foo"):
      xb.local_devices(backend="foo")

  @mock.patch('jax.lib.xla_client.make_tpu_client', side_effect=mock_tpu_client)
  def test_timer_tpu_warning(self, _):
    with warnings.catch_warnings(record=True) as w:
      warnings.simplefilter('always')
      xb.tpu_client_timer_callback(0.01)
      self.assertLen(w, 1)
      msg = str(w[-1].message)
      self.assertIn('Did you run your code on all TPU hosts?', msg)


if __name__ == "__main__":
  absltest.main(testLoader=jtu.JaxTestLoader())
