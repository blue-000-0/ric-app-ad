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
import time
import pandas as pd
from influxdb import DataFrameClient
from configparser import ConfigParser
from mdclogpy import Logger
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError
from requests.exceptions import RequestException, ConnectionError
import json
import os
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

logger = Logger(name=__name__)


class DATABASE(object):
    r""" DATABASE takes an input as database name. It creates a client connection
      to influxDB and It reads/ writes UE data for a given dabtabase and a measurement.


    Parameters
    ----------
    host: str (default='r4-influxdb.ricplt.svc.cluster.local')
        hostname to connect to InfluxDB
    port: int (default='8086')
        port to connect to InfluxDB
    username: str (default='root')
        user to connect
    password: str (default='root')
        password of the use

    Attributes
    ----------
    client: influxDB client
        DataFrameClient api to connect influxDB
    data: DataFrame
        fetched data from database
    """
    
    def __init__(self, dbname='Timeseries', user='root', password='root', host="r4-influxdb.ricplt", port='8086', path='', ssl=False):
        self.data = None
        self.host = "r4-influxdb-influxdb2.ricplt"
        self.port = '80'
        self.user = 'admin'
        self.password = '7jQCNdujbSKju7cL32IzOOwAx7rEjEGJ'
        self.path = path
        self.ssl = ssl
        self.dbname = dbname
        self.client = None
        self.config()
        self.token = 'Eki592tJqjTB47A3KHBpbFpfIoecPVjd'
        self.address = 'http://r4-influxdb-influxdb2.ricplt:80'
        self.org = 'my-org'
        self.bucket = 'kpimon'

    def connect(self):
        if self.client is not None:
            self.client.close()

        try:
            self.client = influxdb_client.InfluxDBClient(url=self.address, token=self.token, org=self.org)
            version = self.client.version()
            logger.info("Conected to Influx Database, InfluxDB version : {}".format(version))
            return True

        except (RequestException, InfluxDBClientError, InfluxDBServerError, ConnectionError):
            logger.error("Failed to establish a new connection with InflulxDB, Please check your url/hostname")
            time.sleep(120)

    def read_data(self, train=False, valid=False, limit=False):
        """Read data method for a given measurement and limit

        Parameters
        ----------
        meas: str (default='ueMeasReport')
        limit:int (defualt=False)
        """
        self.data = None
        query = 'from(bucket:"{}")'.format(self.bucket)
        if not train and not valid and not limit:
            query += ' |> range(start: -1600ms)'
        elif train:
            query += ' |> range(start: -24h, stop: now()) '
            query += ' |> filter(fn: (r) => r["_measurement"] == "UeMetrics") '
            query += ' |> aggregateWindow(every: 1h, fn: mean) '
            query += ' |> sort(columns: ["_time"], desc:true ) |> limit(n: 1)'
            query += ' |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value") '
            logger.info(" Query Command:{}" .format(query))
        elif valid:
            query += ' |> range(start: -5m)'
        elif limit:
            query += ' |> range(start: -1m limit)'+str(limit)
        result = self.query(query)
        if result and len(result[self.meas]) != 0:
            self.data = result[self.meas]

    def write_anomaly(self, df, meas='AD'):
        """Write data method for a given measurement

        Parameters
        ----------
        meas: str (default='AD')
        """
        try:
            self.client.write_api(df, meas)
        except (RequestException, InfluxDBClientError, InfluxDBServerError) as e:
            logger.error('Failed to send metrics to influxdb')
            print(e)

    def query(self, query):
        try:
            query_api = self.client.query_api()
            result = query_api.query(org=self.org, query=query)
        except (RequestException, InfluxDBClientError, InfluxDBServerError, ConnectionError) as e:
            logger.error('Failed to connect to influxdb: {}'.format(e))
            result = False
        return result

    def config(self):
        cfg = ConfigParser()
        cfg.read('src/ad_config.ini')
        for section in cfg.sections():
            if section == 'influxdb':
                self.influxDBAdres = cfg.get(section, "influxDBAdres")
                self.host = cfg.get(section, "host")
                self.port = cfg.get(section, "port")
                self.user = cfg.get(section, "user")
                self.password = cfg.get(section, "password")
                self.path = cfg.get(section, "path")
                self.ssl = cfg.get(section, "ssl")
                self.dbname = cfg.get(section, "database")
                self.meas = cfg.get(section, "measurement")
                self.token = cfg.get(section, "token")
                self.org = cfg.get (section, "org")
                self.bucket = cfg.get(section, "bucket")

            if section == 'features':
                self.thpt = cfg.get(section, "thpt")
                self.rsrp = cfg.get(section, "rsrp")
                self.rsrq = cfg.get(section, "rsrq")
                self.rssinr = cfg.get(section, "rssinr")
                self.prb = cfg.get(section, "prb_usage")
                self.ue = cfg.get(section, "ue")
                self.anomaly = cfg.get(section, "anomaly")


class DUMMY(DATABASE):

    def __init__(self):
        super().__init__()
        self.ue_data = pd.read_csv('src/ue.csv')

    def connect(self):
        return True

    def read_data(self, train=False, valid=False, limit=100000):
        if not train:
            self.data = self.ue_data.head(limit)
        else:
            self.data = self.ue_data.head(limit).drop(self.anomaly, axis=1)

    def write_anomaly(self, df, meas_name='AD'):
        pass

    def query(self, query=None):
        return {'UEReports': self.ue_data.head(1)}
