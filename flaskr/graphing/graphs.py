import numpy as np
import seaborn
import io
import base64
import pandas as pd
import time
import sys
import matplotlib
matplotlib.use('Agg')

from matplotlib import pyplot as plt
from flaskr.model.helpers.functions import saveImage, get_unique_group, get_unique, get_unique_name
from flaskr.database.dataset_models.repository import Repository


def setGraphSettings():
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


class Grapher:
    def __init__(
            self,
            dataset_id: str,
            customtitle: str = ''
    ):
        self.dataset_id = dataset_id
        self.customtitle = customtitle
        self.time = []
        self.data = {}
        self.graph_urls = {}

    def execute(self):
        setGraphSettings()

        startpd = time.time()
        dataset_repository = Repository()
        dataset = dataset_repository.get_by_id(self.dataset_id)
        df = dataset.get_pd_well_collection()
        rfudf = df.copy()
        # testdf = df.copy()
        for i in range(len(rfudf['RFUs'][0])):
            self.time.append(df['cycle'][0]*i)
            # rfudf[df['cycle'][0]*i] = [x[i] for x in rfudf['RFUs']]
        # rfudf = pd.melt(rfudf, id_vars=list(rfudf.columns)[:14],
        #                 value_vars=list(rfudf.columns)[-(len(df['cycle'])):],
        #                 var_name='time',
        #                 value_name='rfu')
        for inf in range(4):
            df['Inflection ' + str(inf)] = [x[inf] if len(x) == 4 else 0 for x in df['inflections']]
            df['Percent Diff ' + str(inf)] = [x[inf] if len(x) == 4 else 0 for x in df['percentdiffs']]
        df = pd.melt(df, id_vars=list(df.columns)[:-8],
                     value_vars=list(df.columns)[-8:],
                     var_name='variable',
                     value_name='value')
        print('pdtest: ', time.time() - startpd)

        startgraphing = time.time()
        self.RFUIndividualGraphsByGroup(rfudf)
        print('1', time.time() - startgraphing)
        self.RFUAverageGraphsByGroup(rfudf)
        print('2', time.time() - startgraphing)
        self.RFUAllGraphs(rfudf)
        print('3', time.time() - startgraphing)

        self.InflectionGraphByGroup(df[df['variable'].str.startswith('Inflection')])
        print('4', time.time() - startgraphing)
        self.InflectionGraphsByNumber(df[df['variable'].str.startswith('Inflection')])
        print('5', time.time() - startgraphing)
        self.percentGraphs(df[df['variable'].str.startswith('Percent Diff ')])
        print('6', time.time() - startgraphing)

        print('graphs finished: ', time.time() - startpd)
        return self.graph_urls

    def InflectionGraphByGroup(self, df):
        for group in range(1, int(df['group'].max())+1):
            subinf = df[(df['group'] == group)].sort_values(['triplicate'])
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
        df.insert(0, 'triplicateIndex', int(df['group'].max())*(df['triplicate'] % 8)+df['group'])
        df = df.sort_values(by=['triplicateIndex', 'sample', 'triplicate', 'group'], ascending=True)
        df['label'] = [x[:-2] for x in df['label']]
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


    def RFUIndividualGraphsByGroup(self, df):
        for group in range(1, int(df['group'].max())+1):
            for idx, row in enumerate(df[df['group'] == group].iterrows()):
                index = row[0]
                seaborn.lineplot(x=self.time, y=row[1]['RFUs'], hue=row[1]['triplicate'], units=index, estimator=None,
                                 linewidth=.7)
            plt.ylabel('RFU')
            plt.xlabel('Time (Min)')
            self.saveimage(plt, 'Individuals_' + str(group))

    def RFUAverageGraphsByGroup(self, df):
        for group in range(1, int(df['group'].max())+1):
            groupdf = df[df['group'] == group]
            for triplicate in get_unique_name(groupdf['label']):
                tdf = groupdf[groupdf['label'] == triplicate]
                sub2df = pd.DataFrame([x[1]['RFUs'] for x in tdf.iterrows()])
                seaborn.lineplot(self.time, sub2df.mean(0), label=triplicate, linewidth=.7)
            plt.ylabel('RFU')
            plt.xlabel('Time (Min)')
            self.saveimage(plt, 'Averages_' + str(group))

    def RFUAllGraphs(self, df):
        for idx, row in enumerate(df.iterrows()):
            print(row[1]['group'])
            seaborn.lineplot(x=self.time, y=row[1]['RFUs'], hue=row[1]['group'], units=idx, estimator=None,
                             linewidth=.7)
        # seaborn.lineplot(x='time', y='rfu', hue='group', units='excelheader', estimator=None, data=df,
        #                  palette=manualcolors[-np.max(df['group']):], linewidth=.7)  # hue='group', units='triplicate'
        plt.ylabel('RFU')
        plt.xlabel('Time (Min)')
        self.saveimage(plt, 'Averages_All')

    def percentGraphs(self, df):
        for group in range(1, int(df['group'].max())+1):
            subpc = df[df['group'] == group]
            indplt = seaborn.swarmplot(x='variable', y="value", hue="label", data=subpc, dodge=True, marker='o',
                                           s=2.6, edgecolor='black', linewidth=.6)
            indplt.set(xticklabels='') #TODO: figure out appropriate labeling
            box = plt.gca().get_position()
            plt.gca().set_position([box.x0, box.y0, box.width * 0.75, box.height])
            plt.legend(bbox_to_anchor=(1, 1), loc='upper left', borderaxespad=0.)
            plt.xlabel('')
            plt.ylabel('Percent Difference from Control')
            self.saveimage(plt, 'PercentDiff_' + str(group))

    def saveimage(self, plt, title):
        plt.title(title, fontsize=14)
        sio = io.BytesIO()
        plt.savefig(sio, format='png')
        plt.close()
        self.graph_urls[title + '.png'] = base64.b64encode(sio.getvalue()).decode('utf-8').replace('\n', '')





