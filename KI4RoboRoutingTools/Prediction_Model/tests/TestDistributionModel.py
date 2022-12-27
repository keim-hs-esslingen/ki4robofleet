import unittest
from Python_Tools.Prediction_Model.Algorithms.Distribution.sector_distribution_model import SectorDistributionModel
from Python_Tools.Prediction_Model.Algorithms.Distribution.distribution_plotter import plot_heatmaps
import pandas as pd

TARGET_MODEL = pd.DataFrame(data=[[0.1, 0.2], [0.6, 0.1]], index=[0.0, 1.0], columns=[0.0, 1.0])
CURRENT_MODEL = pd.DataFrame(data=[[0.3, 0.3], [0.3, 0.1]], index=[0.0, 1.0], columns=[0.0, 1.0])

DIFF_MODEL = pd.DataFrame(data=[[1.0, 0.0, 0.3], [1.0, 1.0, 0.0], [0.0, 1.0, -0.1], [0.0, 0.0, -0.2]], index=[2, 3, 1, 0], columns=['ROW', 'COL', 'DIFF'])

class TestDistributionModel(unittest.TestCase):
    def test_equality(self):
        dist = SectorDistributionModel(target=TARGET_MODEL, current=CURRENT_MODEL)
        diff = dist.diff_list()
        print(f"diff:\n{diff}\ndtypes:\n{diff.dtypes}")
        print(f"diff static:\n{DIFF_MODEL}\ndtypes:\n{DIFF_MODEL.dtypes}")
        pd.testing.assert_frame_equal(diff, DIFF_MODEL)

    def test_attribute_error(self):
        with self.assertRaises(AttributeError):
            SectorDistributionModel(target=TARGET_MODEL, current=pd.DataFrame())


    def test_plot_heatmaps(self):
        dist = SectorDistributionModel(target=TARGET_MODEL, current=CURRENT_MODEL)
        plot_heatmaps(model=dist)


if __name__ == '__main__':
    unittest.main()
