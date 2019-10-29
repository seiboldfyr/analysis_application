import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn
import pandas as pd
from model.functions import saveImage, getUniqueKeys, getGroupHeaders, getTriplicateIndexes
from flask import flash


class Grapher:
    def __init__(
            self,
            paths: dict = None,
            customtitle: str = '',
            data=None,
            labels=None,
            output=None,
            averageoutput=None,
            errors=None
    ):
        self.paths = paths
        self.customtitle = customtitle
        self.data = data
        self.labeldict = labels
        self.output = output
        self.averageoutput = averageoutput
        self.errors = errors

    def execute(self):
        self.setGraphSettings()
        try:
            os.mkdir(os.path.join(self.paths['output'], 'graphs'))
        except OSError:
            pass

        Groups = getUniqueKeys([e[1] for e in self.labeldict.values()])
        groupHeaders = getGroupHeaders([welllabel[0] for welllabel in self.labeldict.values()])
        triplicateIndexList = getTriplicateIndexes([welllabel[0] for welllabel in self.labeldict.values()])

        outputdf = pd.DataFrame(dict(index=list(self.labeldict.keys()),
                                     triplicate=triplicateIndexList,
                                     group=[int(e[1]) for e in list(self.labeldict.values())],
                                     label=[e[0] for e in self.labeldict.values()],
                                     inflection1=[value['Inflections'][0] if len(value['Inflections']) == 4 else 0
                                                  for value in self.output.values()],
                                     inflection2=[value['Inflections'][1] if len(value['Inflections']) == 4 else 0
                                                  for value in self.output.values()],
                                     inflection3=[value['Inflections'][2] if len(value['Inflections']) == 4 else 0
                                                  for value in self.output.values()],
                                     inflection4=[value['Inflections'][3] if len(value['Inflections']) == 4 else 0
                                                  for value in self.output.values()]))

        averagedf = pd.DataFrame(dict(label=list(self.averageoutput.keys()),
                                     group=[int(label[-1]) for label in list(self.averageoutput.keys())],
                                     inflection1=[value[0] for value in self.averageoutput.values()],
                                     inflection2=[value[1] for value in self.averageoutput.values()],
                                     inflection3=[value[2] for value in self.averageoutput.values()],
                                     inflection4=[value[3] for value in self.averageoutput.values()]))
        averagedf = averagedf.melt(id_vars=['label', 'group'], var_name='inflection')
        averagedf = averagedf[(averagedf != 'err')]
        averagedf = averagedf.dropna()

        datadf = pd.DataFrame(columns=['index', 'group', 'triplicate', 'time', 'value'])
        for well in self.data.keys():
            if well == 'Time':
                continue
            tripdf = pd.DataFrame(columns=['index', 'group', 'triplicate', 'value'])
            tripdf['index'] = [well for i in range(len(self.data[well]['Values']))]
            tripdf['group'] = [int(self.data[well]['Group']) for i in range(len(self.data[well]['Values']))]
            tripdf['triplicate'] = [self.data[well]['Label'] for i in range(len(self.data[well]['Values']))]
            tripdf['value'] = self.data[well]['Values']
            tripdf.insert(4, 'time', [t / 60 for t in self.data['Time']])
            datadf = datadf.append(tripdf, sort=True)
        for group in getUniqueKeys([e[1] for e in self.labeldict.values()]):
            self.InflectionGraphByGroup(int(group), groupHeaders, outputdf)
            self.RFUIndividualGraphsByGroup(int(group), datadf)
            self.RFUAverageGraphsByGroup(int(group), datadf)
            self.percentGraphs(group, averagedf)
            flash('Graphed ' + str(group) + ' successfully')

        self.InflectionGraphsByNumber(groupHeaders, outputdf)
        self.RFUAllGraphs(datadf.sort_values(['index']))
        return

    def InflectionGraphByGroup(self, group, headers, df):
        idg = df.melt(id_vars=['triplicate', 'group', 'label', 'index'], var_name='inflection')
        idg['inflection'] = idg['inflection'].str.replace(r'inflection', r'').astype('int')
        subinf = idg[(idg['group'] == group)].sort_values(['index', 'inflection', 'triplicate'])
        indplt = seaborn.swarmplot(x="inflection", y="value", hue="label", data=subinf, dodge=True, marker='o',
                                   s=2.6, edgecolor='black', linewidth=.6)
        indplt.set(xticklabels=['Inflection 1', 'Inflection 2', 'Inflection 3', 'Inflection 4'])
        box = plt.gca().get_position()
        plt.gca().set_position([box.x0, box.y0, box.width * 0.75, box.height])
        legend1 = plt.legend(bbox_to_anchor=(1, 1), loc='upper left', borderaxespad=0.)
        ax = plt.gca().add_artist(legend1)
        plt.legend(['Group  ' + str(idx + 1) + '- ' + str(label) for idx, label in enumerate(headers)],
                   bbox_to_anchor=(1, .1), loc='lower left')
        plt.xlabel('')
        plt.ylabel('Time (Min)')
        saveImage(self, plt, 'Inflections_' + str(group))

    def InflectionGraphsByNumber(self, headers, df):
        gd = df.sort_values(by=['triplicate', 'group'], ascending=True)
        gd['triplicateIndex'] = int(gd['group'].max())*(gd['triplicate'] % 8)+gd['group']
        gd['label'] = [x[:-2] for x in gd['label']]
        gd = gd.sort_values(by=['triplicateIndex', 'index', 'triplicate', 'group'], ascending=True)
        # gd = removeBadWells(badWells,gd,'index')
        numGroups = int(gd['group'].max())
        xaxis = [i + 1 for i in range(numGroups)]
        xaxis = xaxis * int(len(df['index']) / numGroups)
        # plt.legend(handles=handles[1:], labels=[label+'-'+group for label,group in zip(labels[1:],groupHeaders)])
        for inf in range(4):
            indplt = seaborn.swarmplot(x="triplicateIndex", y='inflection' + str(inf + 1), hue="label", data=gd,
                                       marker='o', s=2.6, edgecolor='black', linewidth=.6)
            indplt.set(xticklabels=xaxis)
            plt.ylabel('Time (Min)')
            plt.xlabel('Group Number')
            box = plt.gca().get_position()
            plt.gca().set_position([box.x0, box.y0, box.width * 0.75, box.height])
            legend1 = plt.legend(bbox_to_anchor=(1, 1), loc='upper left')
            ax = plt.gca().add_artist(legend1)
            plt.legend(['Group  ' + str(idx + 1) + '- ' + str(label) for idx, label in enumerate(headers)],
                       bbox_to_anchor=(1, .1), loc='lower left')
            saveImage(self, plt, 'Inflection' + str(inf + 1))

    def RFUIndividualGraphsByGroup(self, group, df):
        df = df[df['group'] == group]
        seaborn.lineplot(x='time', y='value', hue='triplicate', units='index', estimator=None, data=df,
                         linewidth=.7)
        plt.ylabel('RFU')
        plt.xlabel('Time (Min)')
        saveImage(self, plt, 'Individuals_' + str(group))

    def RFUAverageGraphsByGroup(self, group, df):
        df = df[df['group'] == group]
        for triplicate in getUniqueKeys([welllabel[0] for welllabel in self.labeldict.values()]):
            if int(triplicate[-1]) == group:
                subdf = df[df['triplicate'] == triplicate]
                seaborn.lineplot(subdf['time'], subdf.mean(1), label=triplicate, linewidth=.7)
        plt.ylabel('RFU')
        plt.xlabel('Time (Min)')
        saveImage(self, plt, 'Averages_' + str(group))

    def RFUAllGraphs(self, df):
        manualcolors = ["gray", "darkgreen", "cyan", "gold", "dodgerblue", "red", "lime", "magenta"]
        seaborn.lineplot(x='time', y='value', hue='group', units='index', estimator=None, data=df,
                         palette=manualcolors[:np.max(df['group'])], linewidth=.7)  # hue='group', units='triplicate'
        plt.ylabel('RFU')
        plt.xlabel('Time (Min)')
        saveImage(self, plt, 'Averages_All')

    def percentGraphs(self, group, df):
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


    def setGraphSettings(self):
        params = {'legend.fontsize': 5,
                  'legend.loc': 'best',
                  'legend.framealpha': 0.5,
                  'figure.dpi': 300,
                  'legend.handlelength': .8,
                  'legend.markerscale': .4,
                  'legend.labelspacing': .4,
                  'font.size': 8}
        plt.rcParams.update(params)
        manualcolors = ["gray", "darkgreen", "cyan", "gold", "dodgerblue", "red", "lime", "magenta"]
        seaborn.set_palette(manualcolors)




