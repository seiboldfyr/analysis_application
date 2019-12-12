import xlsxwriter
import os
import sys
import pandas as pd
from flaskr.filewriter.helper import addTimeMeasurements

from flaskr.database.dataset_models.repository import Repository


class Writer:
    def __init__(self,
                 excelwriter: pd.ExcelWriter,
                 dataset_id: str):
        self.excelwriter = excelwriter
        self.dataset_id = dataset_id
        self.time = []
        self.workbook = None

    def writebook(self):
        dataset_repository = Repository()
        dataset = dataset_repository.get_by_id(self.dataset_id)
        df = dataset.get_pd_well_collection()
        df = df[(df['is_valid'] == True)]
        for i in range(len(df['RFUs'][0])):
            self.time.append(df['cycle'][0] * i / 60)
        for inf in range(4):
            df['Inflection ' + str(inf + 1)] = [x[inf] if len(x) == 4 else 0 for x in df['inflections']]
            df['Inflection RFU ' + str(inf + 1)] = [x[inf] if len(x) == 4 else 0 for x in df['inflectionRFUs']]
            df['Percent Diff ' + str(inf + 1)] = [x[inf] if len(x) == 4 else 0 for x in df['percentdiffs']]

        variablecolumns =  [4, 14, 17, 20, 23, 15, 18, 21, 24, 16, 19, 22, 25]
        self.vertically_spaced_groups(df, variablecolumns, 'Inflections')

        adf = pd.DataFrame(columns=df.columns.tolist())
        for triplicate in range(1, int(df['triplicate'].max()) + 1):
            gdf = df[(df['triplicate'] == triplicate)].groupby('label').mean()
            adf = pd.concat([adf, gdf], sort=False)
        for group in range(1, int(adf['group'].max()) + 1):
            gdf = adf[(adf['group'] == group)]
            #TODO: control = df['label'].str.endswith('_0')
            control = gdf[gdf['triplicate'] == gdf['triplicate'].min()]
            for inf in range(4):
                inf_label = 'Inflection ' + str(inf + 1)
                #TODO: fix this - adf[inf_label] isn't working as list comprehension
                gdf.loc[:, 'Difference from control ' + str(inf + 1)] = adf[inf_label] - control[inf_label]
                for triplicateA in gdf['triplicate']:
                    rowA = gdf[gdf['triplicate'] == triplicateA]
                    for triplicateB in gdf['triplicate']:
                        if triplicateB < triplicateA:
                            continue
                        rowB = gdf[gdf['triplicate'] == triplicateB]
                        gdf.loc[:, str(triplicateA) + '-' + str(triplicateB)] = float(rowA[inf_label]) + float(rowB[inf_label])
                        triplicateA = triplicateB

            c = len(gdf.columns)
            for n in range(26, c):
                variablecolumns.append(n)
            gdf = gdf.iloc[:, variablecolumns]
            gdf.to_excel(self.excelwriter, sheet_name='Averages', startrow=(group-1)*(gdf.shape[0]+3))

        print(adf.iloc[0])

        return df

    def vertically_spaced_groups(self, df, columns, sheetname):
        for group in range(1, int(df['group'].max()) + 1):
            gdf = df[(df['group'] == group)]
            gdf = gdf.iloc[:, columns]
            gdf.to_excel(self.excelwriter, sheet_name=sheetname, startrow=(group-1)*(gdf.shape[0]+3))
