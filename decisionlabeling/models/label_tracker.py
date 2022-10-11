import os
import pandas as pd
from scipy.signal import savgol_filter


class PosColumns:
    # COLUMN_NAMES = ['L_ankle', 'R_ankle', 'S_tail', 'E_tail']
    COLUMN_NAMES = ['head', 'L_shoulder', 'R_shoulder', 'S_tail', 'L_hip', 'R_hip']


class LabelTracker:

    def __init__(self, state):
        self.state = state
        self.x_arr = []
        self.y_arr = []
        self.df = pd.DataFrame()
        self.labelled_csv_file = os.path.dirname(self.state.file_names[0]) + '.csv'
        self.read_preprocess_df()
        self.savol_length = 150

    @staticmethod
    def df_from_csv(labelled_csv_file):
        data = pd.read_csv(labelled_csv_file, skiprows=1)
        return data

    def read_preprocess_df(self):
        data = self.df_from_csv(self.labelled_csv_file)
        self.df = data[1:].reset_index(drop=True).astype(float)
        self.remove_noise()
        self.df['avg_x'] = self.df[PosColumns.COLUMN_NAMES].mean(axis=1)
        self.df['avg_y'] = self.df[[col + '.1' for col in PosColumns.COLUMN_NAMES]].mean(axis=1)

    def get_coords(self, index):
        return int(self.df.loc[index, 'avg_x']), int(self.df.loc[index, 'avg_y'])

    def get_total_labelled_frames(self):
        return len(self.df)

    def remove_noise(self):
        for column in [col + '.1' for col in PosColumns.COLUMN_NAMES] + PosColumns.COLUMN_NAMES:
            self.df[column] = savgol_filter(self.df[column].values, 150, 2)
