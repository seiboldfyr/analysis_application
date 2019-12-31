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
        self.rowshift = 0
        self.columnshift = 0

    def writebook(self):
        dataset_repository = Repository()
        dataset = dataset_repository.get_by_id(self.dataset_id)
        df = dataset.get_pd_well_collection()
        df = self.build_dataframe(df)

        variablesofinterest = 12
        variablecolumns = [15 + n for n in range(variablesofinterest)]
        variablecolumns.insert(0, 4)
        for group in range(1, int(df['group'].max()) + 1):
            self.write_to_sheet('Inflections', df[(df['group'] == group)], variablecolumns)
            self.rowshift += df[(df['group'] == group)].shape[0] + 4

        adf = self.build_averages(df)
        variablecolumns.pop(0)
        for group in range(1, int(adf['group'].max()) + 1):
            columns = [n for n in variablecolumns]
            gdf = adf[(adf['group'] == group)]
            #TODO: control = df['label'].str.endswith('_0')
            control = gdf[gdf['triplicate'] == gdf['triplicate'].min()]
            for inf in range(4):
                columns.append(variablesofinterest+14+inf)
                inf_label = 'Inflection ' + str(inf + 1)
                gdf.insert(variablesofinterest+14+inf, 'Difference from control ' + str(inf + 1), adf[inf_label] - float(control[inf_label]))
            gdf = gdf.iloc[:, columns]
            gdf.to_excel(self.excelwriter, sheet_name='Averages', startrow=(group-1)*(gdf.shape[0]+3))
            self.excel_formatting('Averages', gdf, 0)

        self.rowshift = 0
        for group in range(1, int(adf['group'].max()) + 1):
            gdf = adf[(adf['group'] == group)]
            pdf = adf[(adf['group'] == group)]
            for inf in range(4):
                columns = []
                inf_label = 'Inflection ' + str(inf + 1)
                pcnt_label = 'Percent Diff ' + str(inf + 1)
                columns.append(6)
                for triplicateA in gdf['triplicate'].unique():
                    columns.append(len(gdf.columns))
                    rowA = gdf[gdf['triplicate'] == triplicateA]
                    gdf.insert(len(gdf.columns), str(len(columns) - 2) + ' ' + inf_label,
                               [label - float(rowA[inf_label]) if triplicateB <= triplicateA else 'nan'
                                for label, triplicateB in zip(gdf[inf_label], gdf['triplicate'])])
                    pdf.insert(len(pdf.columns), str(len(columns) - 2) + ' ' + pcnt_label,
                               [label - float(rowA[pcnt_label]) if triplicateB >= triplicateA else 'nan'
                                for label, triplicateB in zip(pdf[pcnt_label], pdf['triplicate'])])
                spacedifferencematrices = (len(columns)+4) * inf
                self.write_to_sheet('Inf Differences', gdf, columns, spacedifferencematrices)
                self.write_to_sheet('Percent Differences', pdf, columns, spacedifferencematrices)
            self.rowshift += gdf.shape[0] + 4
        return Response(True, '')

    def build_dataframe(self, df):
        for i in range(len(df['RFUs'][0])):
            self.time.append(df['cycle'][0] * i/60)
        for inf in range(4):
            df['Inflection ' + str(inf + 1)] = [x[inf] if len(x) == 4 else 0 for x in df['inflections']]
        for inf in range(4):
            df['Inflection RFU ' + str(inf + 1)] = [x[inf] if len(x) == 4 else 0 for x in df['inflectionRFUs']]
        for inf in range(4):
            df['Percent Diff ' + str(inf + 1)] = [x[inf] if len(x) == 4 else 0 for x in df['percentdiffs']]
        return df

    def write_to_sheet(self, sheetname, df, columns, shiftcolumn=0):
        df = df.iloc[:, columns]
        df.to_excel(self.excelwriter, sheet_name=sheetname,
                    startrow=self.rowshift, startcol=shiftcolumn)
        self.excel_formatting(sheetname, df, shiftcolumn)

    def excel_formatting(self, sheetname, df, startcolumn):
        worksheet = self.excelwriter.sheets[sheetname]
        for idx, column in enumerate(df.columns):
            lengths = [len(x) for x in df.loc[:, column].astype('str')]
            lengths.append(len(column))
            maxlength = max(lengths)
            worksheet.set_column(startcolumn+idx, startcolumn+idx+1, maxlength)
        if sheetname != 'Inflections':
            worksheet.set_column(0, 0, 30)
        else:
            worksheet.set_column(0, 0, 10)

    def build_averages(self, df):
        adf = pd.DataFrame(columns=df.columns.tolist())
        for triplicate in range(int(df['triplicate'].max())+1):
            gdf = df[(df['triplicate'] == triplicate)].groupby('label').mean()
            adf = pd.concat([adf, gdf], sort=False)
        return adf

