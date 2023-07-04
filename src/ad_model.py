# ==================================================================================
#  Copyright (c) 2020 HCL Technologies Limited.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# ==================================================================================

import joblib
from mdclogpy import Logger

logger = Logger(name=__name__)


class modelling(object):
    r""" Filter dataframe based on paramters that were used to train model
    use transormer to transform the data
    load model and predict the label(normal/anomalous)

    Parameters:
    data:DataFrame
    """

    def __init__(self, data=None):
        self.data = data
        self.load_model()
        self.load_param()
        self.load_scale()

    def load_model(self):
        try:
            with open('src/model', 'rb') as f:
                self.model = joblib.load(f)
        except FileNotFoundError:
            logger.error("Model Does not exsist")

    def load_param(self):
        try:
            with open('src/num_params', 'rb') as f:
                self.num = joblib.load(f)

        except FileNotFoundError:
            logger.error("Parameter file does not exsist")

    def load_scale(self):
        try:
            with open('src/scale', 'rb') as f:
                self.scale = joblib.load(f)
        except FileNotFoundError:
            logger.error("Scale file does not exsist")

    def transformation(self):
        self.data = self.scale.transform(self.data)

    def predict(self, df):
        """ Load the saved model and return predicted result.
        Parameters
        .........
        name:str
            name of model

        Return
        ......
        pred:int
            predict label on a given sample

        """
        self.data = df.loc[:, self.num]
        self.transformation()
        pred = self.model.predict(self.data)
        pred = [1 if p == -1 else 0 for p in pred]
        return pred


class CAUSE(object):
    r""""Rule basd method to find degradation type of anomalous sample

    Attributes:
    normal:DataFrame
        Dataframe that contains only normal sample
    """

    def __init__(self):
        self.normal = None

    def cause(self, df, db):
        """ Filter normal data for a particular ue-id to compare with a given sample
            Compare with normal data to find and return degradaton type
        """
        sample = df.copy()
        sample.index = range(len(sample))
        for i in range(len(sample)):
            if sample.iloc[i]['Anomaly'] == 1:
                query = 'from(bucket: "kpimon")'
                query += '|> range(start: -20s)' 
                query += '|> filter(fn: (r) => r["_measurement"] == "UeMetrics")'
                query += '|> filter(fn: (r) => r["{}"] == "{}")'.format(db.ue, sample.iloc[i][db.ue])
                query += '|> filter(fn: (r) => r["_field"] == "DRB_UEThpDl" or r["_field"] == "Viavi_UE_Rsrp" or r["_field"] == "Viavi_UE_Rsrq" or r["_field"] == "Viavi_UE_RsSinr" or r["_field"] == "RRU_PrbUsedDl" or r["_field"] == "Viavi_UE_anomalies") '
                query += '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
                normal = db.query(query)
                if len(normal) != 0:
                    normal = normal[[db.thpt, db.rsrp, db.rsrq]]
                    deg = self.find(sample.loc[i, :], normal.max(), db)
                    print('sample')
                    print(sample[db.thpt], sample[db.rsrp], sample[db.rsrq])
                    print('normal')
                    print(normal[db.thpt], normal[db.rsrp], normal[db.rsrq])
                    if deg:
                        print('anomaly')
                        sample.loc[i, 'Degradation'] = deg
                        if 'Throughput' in deg and ('RSRP' in deg or 'RSRQ' in deg):
                            sample.loc[i, 'Anomaly'] = 2
                    else:
                        print('error')
                        sample.loc[i, 'Anomaly'] = 0
        return sample[['Anomaly', 'Degradation']].values.tolist()

    def find(self, row, l, db):
        """ store if a particular parameter is below threshold and return """
        deg = []
        if row[db.thpt] < l[db.thpt]*0.5:
            deg.append('Throughput')
        if row[db.rsrp] < l[db.rsrp]-15:
            deg.append('RSRP')
        if row[db.rsrq] < l[db.rsrq]-10:
            deg.append('RSRQ')
        if len(deg) == 0:
            deg = False
        else:
            deg = ' '.join(deg)
        return deg
