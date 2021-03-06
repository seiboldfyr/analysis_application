import numpy as np
import seaborn
import io
import base64
import pandas as pd
from sklearn.linear_model import LinearRegression
from flask import current_app, flash
import matplotlib
matplotlib.use('Agg')

from matplotlib import pyplot as plt
from flaskr.model.helpers.functions import get_unique_group, get_unique
from flaskr.model.helpers.buildfunctions import get_concentrations
from flaskr.database.dataset_models.repository import Repository
from flaskr.model.helpers.calcfunctions import reg_conc


def removeLegendTitle(plot):
    handles, labels = plot.get_legend_handles_labels()
    plot.legend(handles=handles[1:], labels=labels[1:])
    return plot


def getRegression(df):
    df = df.groupby('triplicate').mean()
    linear_regressor = LinearRegression()
    linear_regressor.fit(np.asarray(np.log(df['pMconcentration'])).reshape(-1, 1),
                         np.asarray(df['value']).reshape(-1, 1))
    rvalue = linear_regressor.score(np.asarray(np.log(df['pMconcentration'])).reshape(-1, 1),
                                    np.asarray(df['value']).reshape(-1, 1))
    return [rvalue, linear_regressor]


class Grapher:
    def __init__(
            self,
            dataset_id: str,
            customtitle: str = '',
    ):
        self.transparent = False
        self.dataset_id = dataset_id
        self.customtitle = customtitle
        self.time = []
        self.data = {}
        self.graph_urls = {}
        self.colors = ["gray",  "dodgerblue", "red", "lightgreen", "magenta", "gold", "cyan", "darkgreen"]
        # TODO: make these colors adaptable when the total number of concentrations =/= 8

    def execute(self, features):
        if features is None:
            features = dict()
        self.setGraphSettings(features)
        dataset_repository = Repository()
        dataset = dataset_repository.get_by_id(self.dataset_id)
        df = dataset.get_pd_well_collection()
        df = df[df['is_valid'] == True]
        self.name = dataset.get_name()

        df = df.drop(columns=['_id', 'dataset_id'])

        rfudf = df.copy()
        for i in range(len(rfudf['RFUs'].iloc[0])):
            self.time.append(i)

        df['DeltaCt'] = [x[0] if len(x) > 0 else 0 for x in df['deltaCt']]
        df['CtThreshold'] = [x[1] if len(x) > 1 else 0 for x in df['deltaCt']]
        df['CtRFU'] = [x[2] if len(x) > 2 else 0 for x in df['deltaCt']]
        for inf in range(4):
            df['Inflection ' + str(inf)] = [dict(x)[str(inf+1)] if dict(x).get(str(inf+1)) else 0 for x in df['inflections']]
            df['RFU of Inflection ' + str(inf)] = [dict(x)[str(inf+1)] if dict(x).get(str(inf+1)) else 0 for x in df['inflectionRFUs']]
            df['Percent Diff ' + str(inf)] = [x[inf] if len(x) == 4 else 0 for x in df['percentdiffs']]

        df = df.drop(columns=['triplicate_id', 'cycle'])

        testdf = df.copy()
        df = df.drop(columns=['RFU of Inflection ' + str(inf) for inf in range(4)])

        df = pd.melt(df, id_vars=list(df.columns)[:-8],
                     value_vars=list(df.columns)[-8:],
                     var_name='variable',
                     value_name='value')

        if features.get('experimental'):
            self.CtThresholds(testdf)

        if features.get('rfus'):
            self.RFUIndividualGraphsByGroup(rfudf, testdf)
            self.RFUGraphs(rfudf)

        if features.get('inflections'):
            self.InflectionGraphByGroup(df[df['variable'].str.startswith('Inflection')])
            self.InflectionGraphsByNumber(df[df['variable'].str.startswith('Inflection')])

        if features.get('curvefits'):
            self.CurveFitByGroup(df[df['variable'].str.startswith('Inflection')])

        if features.get('percentdiffs'):
            self.percentGraphs(df[df['variable'].str.startswith('Percent Diff ')])

        if len(self.graph_urls) < 1:
            self.RFUGraphs(rfudf)

        return [self.graph_urls, self.name]

    def InflectionGraphByGroup(self, df):
        for group in range(1, int(df['group'].max())+1):
            subinf = df[(df['group'] == group)].sort_values(['variable', 'triplicate', 'value'])
            indplt = seaborn.swarmplot(x="variable", y="value", hue="label", data=subinf, dodge=True, marker='o',
                                       s=2.6, linewidth=.6)
            indplt.set(xticklabels=['Inflection 1', 'Inflection 2', 'Inflection 3', 'Inflection 4'])
            indplt = removeLegendTitle(indplt)
            box = plt.gca().get_position()
            plt.gca().set_position([box.x0, box.y0, box.width * 0.75, box.height])
            legend1 = plt.legend(bbox_to_anchor=(1, 1), loc='upper left', borderaxespad=0.)
            try:
                ax = plt.gca().add_artist(legend1)
            except matplotlib.MatplotlibDeprecationWarning:
                current_app.logger.error('Matplotlib depreciation warning with dataset: %s' % self.dataset_id)

            plt.legend(['Group  ' + str(idx + 1) + '- ' + str(label)
                        for idx, label in enumerate(get_unique_group(df['label']))],
                       bbox_to_anchor=(1, .1), loc='lower left')
            plt.xlabel('')
            plt.ylabel('Cycles')
            self.saveimage(plt, 'Inflections_' + str(group))

    def InflectionGraphsByNumber(self, df):
        df.insert(0, 'triplicateIndex', int(df['group'].max())*(df['sample'])+df['group'])
        grouplabels = get_unique_group(df['label'])
        if len([reg_conc(item) for item in df['label'] if reg_conc(item)]) > 0:
            df.insert(0, 'labelwithoutgroup', [reg_conc(item).group(0) for item in df['label']])
        else:
            df.insert(0, 'labelwithoutgroup', df['label'])

        for inf in range(4):
            indplt = seaborn.swarmplot(x="triplicateIndex", y="value", hue="labelwithoutgroup",
                                       data=df[df['variable'] == "Inflection " + str(inf)],
                                       marker='o', s=2.6, linewidth=.6)
            indplt.set(xticklabels=[str(num % 4 + 1) for num in np.arange(32)])
            indplt = removeLegendTitle(indplt)
            plt.ylabel('Cycles')
            plt.xlabel('Group Number')
            box = plt.gca().get_position()
            plt.gca().set_position([box.x0, box.y0, box.width * 0.75, box.height])
            legend1 = plt.legend(bbox_to_anchor=(1, 1), loc='upper left')
            try:
                ax = plt.gca().add_artist(legend1)
            except matplotlib.MatplotlibDeprecationWarning:
                current_app.logger.error('Matplotlib depreciation with dataset: %s' % self.dataset_id)

            plt.legend(['Group  ' + str(idx + 1) + '- ' + str(label)
                        for idx, label in enumerate(grouplabels)],
                       bbox_to_anchor=(1, .1), loc='lower left')
            self.saveimage(plt, 'Inflection' + str(inf + 1))

    def RFUIndividualGraphsByGroup(self, df, idf):
        for group in range(1, int(df['group'].max())+1):
            rdf = pd.DataFrame(columns=['time', 'rfus', 'triplicate', 'index'])
            for idx, row in enumerate(df[df['group'] == group].iterrows()):
                tdf = pd.DataFrame(dict(time=self.time, rfus=row[1]['RFUs'], triplicate=row[1]['triplicate'],
                                        index=row[0], label=row[1]['label']))
                rdf = pd.concat([rdf, tdf], sort=False)

            iidf = idf[(idf['group'] == group)]
            for i in range(4):
                if not self.validateDF(iidf[iidf["RFU of Inflection " + str(i)] > 0]):
                    continue
                plt.scatter(x="Inflection "+str(i), y="RFU of Inflection "+str(i), label="Inflection " + str(i+1),
                            data=iidf[iidf["RFU of Inflection " + str(i)] > 0], s=10, edgecolor='black', linewidth=.2)

            snsplot = seaborn.lineplot(x='time', y='rfus', hue='label', units='index', estimator=None,
                                       data=rdf, linewidth=.7)
            snsplot = removeLegendTitle(snsplot)
            plt.ylabel('RFU')
            plt.xlabel('Cycles')
            self.saveimage(plt, 'Individuals_' + str(group))

    def RFUGraphs(self, df):
        for group in range(1, int(df['group'].max())+1):
            adf = pd.DataFrame(columns=['time', 'averagerfu', 'triplicate', 'label', 'group'])  # changed here
            groupdf = df[df['group'] == group]
            grouplabel = groupdf.iloc[0]['label']
            for idx, triplicate in enumerate(get_unique(groupdf['label'])):
                tdf = groupdf[groupdf['label'] == triplicate]
                tdf = pd.DataFrame([x[1]['RFUs'] for x in tdf.iterrows()])
                tdf = pd.DataFrame(data=dict(time=self.time,
                                             averagerfu=tdf.mean(0),
                                             label=triplicate,
                                             triplicate=idx,
                                             group=group))
                adf = pd.concat([adf, tdf], sort=False)
            plt.figure(0)
            grouprfuplot = seaborn.lineplot(x='time', y='averagerfu', hue='label', units='triplicate', estimator=None,
                                            data=adf, linewidth=.7)
            grouprfuplot = removeLegendTitle(grouprfuplot)
            plt.ylabel('RFU')
            plt.xlabel('Cycles')
            self.saveimage(plt, 'Averages_' + str(group))

            plt.figure(1)
            allrfuplot = seaborn.lineplot(x='time', y='averagerfu', data=adf, units='triplicate', estimator=None,
                                          linewidth=.7, legend="full", label=grouplabel)
            allrfuplot = removeLegendTitle(allrfuplot)
        [h, l] = allrfuplot.get_legend_handles_labels()
        unique_label_index = np.unique([x.split('_')[-1] for x in l], return_index=True)[1]
        h = [x for idx, x in enumerate(h) if idx in unique_label_index]
        allrfuplot.legend(handles=h)

        plt.ylabel('RFU')
        plt.xlabel('Cycles')
        self.saveimage(plt, 'Averages_All')

    def percentGraphs(self, df):
        for group in range(1, int(df['group'].max())+1):
            subpc = df[df['group'] == group]
            if not self.validateDF(subpc[subpc['value'] > 0]):
                continue
            indplt = seaborn.swarmplot(x='variable', y="value", hue="label", data=subpc, dodge=True, marker='o',
                                       s=2.6, linewidth=.6)
            indplt.set(xticklabels=[str(num+1) for num in np.arange(4)])
            box = plt.gca().get_position()
            plt.gca().set_position([box.x0, box.y0, box.width * 0.75, box.height])
            plt.legend(bbox_to_anchor=(1, 1), loc='upper left', borderaxespad=0.)
            plt.xlabel('')
            plt.ylabel('Percent Difference from Control')
            self.saveimage(plt, 'PercentDiff_' + str(group))

    def CurveFitByGroup(self, df):              # TODO: Figure out vertical shift in curve-fitting, see 20200110b_AA output
        for group in range(1, int(df['group'].max()) + 1):
            cdf = df[(df['group'] == group) & df['value'] > 0].sort_values(['triplicate', 'value'])
            if len([get_concentrations(reg_conc(item).group(0)) for item in cdf['label'] if reg_conc(item)]) == 0:
                flash('The concentration cannot be identified for curve fit graphs', 'error')
                break
            cdf.insert(0, 'pMconcentration', [get_concentrations(reg_conc(item).group(0))
                                              for item in cdf['label']])
            cdf = cdf[cdf['pMconcentration'] >= .1]
            for inf in range(4):
                infcdf = cdf[cdf['variable'] == "Inflection " + str(inf)]
                if not self.validateDF(infcdf):
                    continue
                curveplt = seaborn.swarmplot(x="pMconcentration", y="value",
                                             data=infcdf, marker='o', s=2.6,
                                             palette=["black"], linewidth=.6)

                [rvalue, linear_regressor] = getRegression(infcdf)

                #get rvalue not including the .1pM concentration
                lessrvalue = 'nan'
                if self.validateDF(infcdf[(infcdf['pMconcentration'] >= 1)]):
                    [lessrvalue, _] = getRegression(infcdf[(infcdf['pMconcentration'] >= 1)])
                    lessrvalue = round(lessrvalue, 5)

                concentrationX = [.01, .1, 1, 10, 100, 1000, 10000]
                Y = linear_regressor.predict(np.log(concentrationX).reshape(-1, 1)).flatten()
                label = 'Inflection ' + str(inf + 1) + ' ' + \
                        str(round(float(linear_regressor.coef_[0]), 4)) + 'x + ' + \
                        str(round(float(linear_regressor.intercept_), 4)) + \
                        ' Rvalue: ' + str(round(rvalue, 5)) + \
                        ' (' + str(lessrvalue) + ')'

                curveplt = seaborn.lineplot(x=[-1, 0, 1, 2, 3, 4, 5], y=Y, label=label)
                plt.ylabel('Cycles')
                plt.xlabel('Log of Concentration (pM)')
            self.saveimage(plt, 'CurveFit_' + str(group))

    def CtThresholds(self, df):
        for group in range(1, int(df['group'].max())+1):
            idf = df[(df['group'] == group)]
            ctRFU = idf[idf['CtRFU'] > 0]['CtRFU']
            if not self.validateDF(ctRFU) or len(np.unique(idf['concentration'])) == 1:
                flash('Unique concentration cannot be identified in group %s for ct threshold graphs' % group, 'error')
                continue

            plt.scatter(x='concentration', y='DeltaCt', label='concentration',
                        data=idf, s=10, edgecolor='black', linewidth=.2)
            plt.ylabel('Delta Ct (difference in minutes)')
            plt.xlabel('Concentration')
            self.saveimage(plt, 'DeltaCt_' + str(group))

            plt.scatter(x='CtThreshold', y='concentration',  label='concentration',
                        data=idf, s=10, edgecolor='black', linewidth=.2)
            plt.xlabel('Ct value (Minutes until ' + str(round(ctRFU.iloc[0], 2)) + ' RFUs are surpassed)')
            plt.ylabel('Concentration')
            self.saveimage(plt, 'Ct_' + str(group))

    def validateDF(self, df):
        if len(df) > 0:
            return True
        return False

    def saveimage(self, plt, title):
        plt.title(self.name + '_' + title, fontsize=14)
        sio = io.BytesIO()
        plt.savefig(sio, format='png', transparent=self.transparent)
        plt.close()
        self.graph_urls[self.name +'_' + title + '.png'] = base64.b64encode(sio.getvalue()).decode('utf-8').replace('\n', '')

    def setGraphSettings(self, features):
        if features.get('transparent'):
            self.transparent = True

        params = {'legend.fontsize': 5,
                  'legend.loc': 'best',
                  'legend.framealpha': 0.5,
                  'figure.dpi': 250,
                  'legend.handlelength': .8,
                  'legend.markerscale': .4,
                  'legend.labelspacing': .4,
                  'font.size': 8}

        if features.get('white'):
            params.update({
                  'scatter.edgecolors': 'white',
                  'axes.edgecolor': 'white',
                  'axes.facecolor': 'white',
                  'axes.labelcolor': 'white',
                  'xtick.color': 'white',
                  'ytick.color': 'white',
                  'figure.facecolor': 'white',
                  'text.color': 'white',
                  'legend.framealpha': .1})
        else:
            params.update({
                'scatter.edgecolors': 'black',
                'axes.edgecolor': 'black',
                'axes.facecolor': 'white',
                'axes.labelcolor': 'black',
                'xtick.color': 'black',
                'ytick.color': 'black',
                'figure.facecolor': 'white',
                'text.color': 'black'})

        plt.rcParams.update(params)
        seaborn.set_palette(self.colors)



