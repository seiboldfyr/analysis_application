import numpy as np
import seaborn
import io
import sys
import base64
import pandas as pd
import time
import matplotlib
matplotlib.use('Agg')

from matplotlib import pyplot as plt
from flaskr.model.helpers.functions import saveImage, get_unique_group
from flaskr.model.helpers.buildfunctions import get_collection
from flaskr.database.dataset_models.repository import Repository


class Grapher:
    def __init__(
            self,
            dataset_id: str,
            customtitle: str = '',
            time: list = None
    ):
        self.dataset_id = dataset_id
        self.customtitle = customtitle
        self.time = time
        self.data = {}
        self.graph_urls = {}

    def execute(self):
        self.setGraphSettings()

        startpd = time.time()
        dataset_repository = Repository()
        dataset = dataset_repository.get_by_id(self.dataset_id)
        df = dataset.get_pd_well_collection()
        for inf in range(4):
            df['Inflection ' + str(inf)] = [x[inf] if len(x) == 4 else 0 for x in df['inflections']]
            df['Percent Diff ' + str(inf)] = [x[inf] if len(x) == 4 else 0 for x in df['percentdiffs']]
        df = pd.melt(df, id_vars=list(df.columns)[:-8],
                value_vars=list(df.columns)[-8:],
                var_name='variable',
                value_name='value')
        print('pdtest: ', time.time() - startpd)

        self.InflectionGraphByGroup(df[df['variable'].str.startswith('Inflection')])
        # self.RFUIndividualGraphsByGroup(max(Groups), datadf)
        # self.RFUAverageGraphsByGroup(max(Groups), datadf)
        # self.percentGraphs(max(Groups), averagedf)

        self.InflectionGraphsByNumber(df[df['variable'].str.startswith('Inflection')])
        # self.RFUAllGraphs(datadf.sort_values(['index']))
        print('graphs finished: ', time.time() - startpd)
        return self.graph_urls

    def InflectionGraphByGroup(self, df):
        for group in range(1, int(df['group'].max())+1):
            subinf = df[(df['group'] == group)].sort_values(['triplicate'])
            subinf.head(15)
            indplt = seaborn.swarmplot(x="variable", y="value", hue="label", data=subinf, dodge=True, marker='o',
                                       s=2.6, edgecolor='black', linewidth=.6)
            indplt.set(xticklabels=['Inflection 1', 'Inflection 2', 'Inflection 3', 'Inflection 4'])
            box = plt.gca().get_position()
            plt.gca().set_position([box.x0, box.y0, box.width * 0.75, box.height])
            legend1 = plt.legend(bbox_to_anchor=(1, 1), loc='upper left', borderaxespad=0.)
            ax = plt.gca().add_artist(legend1)
            plt.legend(['Group  ' + str(idx + 1) + '- ' + str(label)
                        for idx, label in enumerate(get_unique_group(df['label']))],
                       bbox_to_anchor=(1, .1), loc='lower left')
            plt.xlabel('')
            plt.ylabel('Time (Min)')
            self.saveimage(plt, 'Inflections_' + str(group))

    def InflectionGraphsByNumber(self, df):
        df['triplicateIndex'] = int(df['group'].max())*(df['triplicate'] % 8)+df['group']
        df['label'] = [x[:-2] for x in df['label']]
        df = df.sort_values(by=['triplicateIndex', 'sample', 'triplicate', 'group'], ascending=True)
        numGroups = int(df['group'].max())
        xaxis = [i + 1 for i in range(numGroups)]
        xaxis = xaxis * int(len(df['sample']) / numGroups)
        for inf in range(4):
            gd = df[df['variable'] == "Inflection " + str(inf)]

            indplt = seaborn.swarmplot(x="triplicateIndex", y="value", hue="label", data=gd,
                                       marker='o', s=2.6, edgecolor='black', linewidth=.6)
            indplt.set(xticklabels=xaxis)
            plt.ylabel('Time (Min)')
            plt.xlabel('Group Number')
            box = plt.gca().get_position()
            plt.gca().set_position([box.x0, box.y0, box.width * 0.75, box.height])
            legend1 = plt.legend(bbox_to_anchor=(1, 1), loc='upper left')
            ax = plt.gca().add_artist(legend1)
            plt.legend(['Group  ' + str(idx + 1) + '- ' + str(label)
                        for idx, label in enumerate(get_unique_group(df['label']))],
                       bbox_to_anchor=(1, .1), loc='lower left')
            self.saveimage(plt, 'Inflection' + str(inf + 1))


    def RFUIndividualGraphsByGroup(self, groups, df):
        for group in range(1, groups+1):
            fig = plt.figure()
            seaborn.lineplot(x='time', y='value', hue='triplicate', units='index', estimator=None, data=df[df['group'] == group],
                             linewidth=.7)
            plt.ylabel('RFU')
            plt.xlabel('Time (Min)')
            saveImage(self, plt, 'Individuals_' + str(group))

    def RFUAverageGraphsByGroup(self, groups, df):
        for group in range(1, groups+1):
            fig = plt.figure()
            groupdf = df[df['group'] == group]
            for triplicate in getUnique([welllabel['label'] for welllabel in self.data.values()]):
                if int(triplicate[-1]) == group:
                    subdf = groupdf[groupdf['triplicate'] == triplicate]
                    seaborn.lineplot(subdf['time'], subdf.mean(1), label=triplicate, linewidth=.7)
            plt.ylabel('RFU')
            plt.xlabel('Time (Min)')
            saveImage(self, plt, 'Averages_' + str(group))

    def RFUAllGraphs(self, df):
        fig = plt.figure()
        manualcolors = ["gray", "darkgreen", "cyan", "gold", "dodgerblue", "red", "lime", "magenta"]
        seaborn.lineplot(x='time', y='value', hue='group', units='index', estimator=None, data=df,
                         palette=manualcolors[-np.max(df['group']):], linewidth=.7)  # hue='group', units='triplicate'
        plt.ylabel('RFU')
        plt.xlabel('Time (Min)')
        saveImage(self, plt, 'Averages_All')

    def percentGraphs(self, groups, df):
        for group in range(1, groups+1):
            fig = plt.figure()
            subpc = df[(df['group'] == group)].sort_values(['inflection'])
            if not subpc.empty:
                indplt = seaborn.swarmplot(x='label', y="value", hue="label", data=subpc, dodge=True, marker='o',
                                           s=2.6, edgecolor='black', linewidth=.6)
                indplt.set(xticklabels='')
                box = plt.gca().get_position()
                plt.gca().set_position([box.x0, box.y0, box.width * 0.75, box.height])
                plt.legend(bbox_to_anchor=(1, 1), loc='upper left', borderaxespad=0.)
                plt.xlabel('')
                plt.ylabel('Percent Difference from Control')
                saveImage(self, plt, 'PercentDiff_' + str(group))

    def saveimage(self, plt, title):
        plt.title(title, fontsize=14)
        sio = io.BytesIO()
        plt.savefig(sio, format='png')
        plt.close()
        self.graph_urls[title + '.png'] = base64.b64encode(sio.getvalue()).decode('utf-8').replace('\n', '')

    def setGraphSettings(self):
        params = {'legend.fontsize': 5,
                  'legend.loc': 'best',
                  'legend.framealpha': 0.5,
                  'figure.dpi': 250,
                  'legend.handlelength': .8,
                  'legend.markerscale': .4,
                  'legend.labelspacing': .4,
                  'font.size': 8}
        plt.rcParams.update(params)
        manualcolors = ["gray", "darkgreen", "cyan", "gold", "dodgerblue", "red", "lime", "magenta"]
        seaborn.set_palette(manualcolors)




