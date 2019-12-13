import pandas as pd
from flaskr.framework.model.request.response import Response

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
        df = self.build_dataframe(df)

        variablecolumns = [14 + n for n in range(12)]
        variablecolumns.insert(0, 4)
        for group in range(1, int(df['group'].max()) + 1):
            self.write_to_sheet('Inflections', df[(df['group'] == group)], variablecolumns, group)

        adf = self.build_averages(df)
        variablecolumns.pop(0)
        for group in range(1, int(adf['group'].max()) + 1):
            columns = [n for n in variablecolumns]
            gdf = adf[(adf['group'] == group)]
            #TODO: control = df['label'].str.endswith('_0')
            control = gdf[gdf['triplicate'] == gdf['triplicate'].min()]
            for inf in range(4):
                columns.append(26+inf)
                inf_label = 'Inflection ' + str(inf + 1)
                gdf.insert(26+inf, 'Difference from control ' + str(inf + 1), adf[inf_label] - float(control[inf_label]))
            gdf = gdf.iloc[:, columns]
            gdf.to_excel(self.excelwriter, sheet_name='Averages', startrow=(group-1)*(gdf.shape[0]+3))
            self.excel_formatting('Averages', gdf)

        for group in range(1, int(adf['group'].max()) + 1):
            columns = []
            gdf = adf[(adf['group'] == group)]
            for inf in range(4):
                inf_label = 'Inflection ' + str(inf + 1)
                for triplicateA in gdf['triplicate'].unique():
                    columns.append(len(gdf.columns))
                    rowA = gdf[gdf['triplicate'] == triplicateA]
                    gdf.insert(len(gdf.columns), str(rowA['label']) + ' ' + inf_label, gdf[inf_label] - float(rowA[inf_label]))
            self.write_to_sheet('Differences', gdf, columns, group)

        return Response(True, '')

    def build_dataframe(self, df):
        df = df[(df['is_valid'] == True)]
        for i in range(len(df['RFUs'][0])):
            self.time.append(df['cycle'][0] * i / 60)
        for inf in range(4):
            df['Inflection ' + str(inf + 1)] = [x[inf] if len(x) == 4 else 0 for x in df['inflections']]
        for inf in range(4):
            df['Inflection RFU ' + str(inf + 1)] = [x[inf] if len(x) == 4 else 0 for x in df['inflectionRFUs']]
        for inf in range(4):
            df['Percent Diff ' + str(inf + 1)] = [x[inf] if len(x) == 4 else 0 for x in df['percentdiffs']]
        return df

    def write_to_sheet(self, sheetname, df, columns, group):
        df = df.iloc[:, columns]
        df.to_excel(self.excelwriter, sheet_name=sheetname, startrow=(group - 1) * (df.shape[0] + 3))
        self.excel_formatting(sheetname, df)

    def excel_formatting(self, sheetname, df):
        worksheet = self.excelwriter.sheets[sheetname]
        maxlength = max(df.astype('str').applymap(lambda x: len(x)).max())
        worksheet.set_column(1, len(df.columns), 2*maxlength/3)

    def build_averages(self, df):
        adf = pd.DataFrame(columns=df.columns.tolist())
        for triplicate in range(1, int(df['triplicate'].max()) + 1):
            gdf = df[(df['triplicate'] == triplicate)].groupby('label').mean()
            adf = pd.concat([adf, gdf], sort=False)
        return adf