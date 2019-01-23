from .common import *

# ------------------------------------------------------------------------------
class GenExpPlot(object):
    """
    Class for Plotly barplots and violins.
    traces = [
        0 : {
            group1: [ values ],
            group2: [ values ],
            ...
        },
        1 :
            ...
    ]
    """
    def __init__(self):
        self.traces = list()
        self.traces_set = set()
        self.groups = list()
        self.groups_set = set()
        self.title  = str()
        self.ylab   = str()
        self.trace_names = list()
        self.units = dict()

    def add_group(self, group):
        if group not in self.groups_set:
            self.groups.append(group)
            self.groups_set.add(group)
        
        for trace in self.traces:
            if group not in trace:
                trace[group] = list()
        
        if not self.traces:
            self.traces.append(dict())

    def add_value(self, value, group, trace=0):
        if group not in self.traces[trace]:
            self.add_group(group)
        self.traces[trace][group].append(value)

    def add_trace(self, trace_idx):
        self.traces.append(dict())
        # Clone groups from other traces
        for group in self.traces[0].keys():
            self.traces[trace_idx][group] = list()

    def add_trace_name(self, trace_idx, name):
        if len(self.trace_names) <= trace_idx:
            self.trace_names.append(name)
        else:
            self.trace_names[trace_idx] = name

    def add_title(self, title):
        self.title = title

    def add_ylab(self, ylab):
        self.ylab = ylab
    
    def is_empty(self):
        empty = True
        for trace in self.traces:
            for condition, expression in trace.items():
                if sum(expression):
                    empty = False
                    break
        return empty
    
    def add_units(self, axis, units):
        '''
        Adds units to one axis of the plot.

        Args:
            axis: string cointaining 'x' or 'y'.
            units: string for units.
        
        Returns:
            nothing
        '''
        if axis == 'x' or axis == 'y':
            self.units[axis] = units
        else:
            raise ValueError("Axis should be a string containing 'x' or 'y'.")
            



# ------------------------------------------------------------------------------
class BarPlot(GenExpPlot):
    """
    Class for Plotly bar plots.
    Each bar (group) consists of only one value.
    """
    def __init__(self):
        super(BarPlot, self).__init__()
    
    def plot(self):
        theplot = dict()
        theplot['data'] = list()
        for trace_idx, trace in enumerate(self.traces):
            trace_data = dict()
            x = list()
            y = list()
            if len(self.trace_names) > trace_idx:
                trace_data['name'] = self.trace_names[trace_idx]
            for group in self.groups:
                x.append(group)
                
                y.append(trace[group][0])
            trace_data['x'] = x
            trace_data['y'] = y
            trace_data['type'] = 'bar'
            theplot['data'].append(trace_data)
        theplot['layout'] = dict()
        if len(self.traces) > 1:
            theplot['layout']['barmode'] = "group"
        
        if self.title:
            theplot['layout']['title'] = self.title
        if self.ylab:
            theplot['layout']['yaxis'] = dict()
            theplot['layout']['yaxis']['title'] = self.ylab
        
        if self.units:
            for axis, units in self.units.items():
                axis_name = axis + 'axis'
                theplot['layout'][axis_name] = dict()
                theplot['layout'][axis_name]['title'] = units
        return theplot
    
    

# ------------------------------------------------------------------------------
class ViolinPlot(GenExpPlot):
    """
    Class for Plotly violinplots.
    Each violin (group) is made of multiple values.
    Class for Plotly barplots.
    traces = [
        0 : {
            group1: [ values ],
            group2: [ values ],
            ...
        },
        1 :
            ...
    ]
    """
    def __init__(self):
        super(ViolinPlot, self).__init__()
    

    def jitter_and_round(self, values, jitter=0.01):
        newvalues = list()
        for idx, value in enumerate(values):
            value = round(value, 3)
            if idx % 2 == 0:
                newvalues.append(value + jitter)
            else:
                newvalues.append(value - jitter)
        return newvalues


    def plot(self):
        theplot = dict()
        theplot['data'] = list()
        for trace_idx, trace in enumerate(self.traces):
            trace_data = dict()
            trace_data['type'] = 'violin'
            trace_data['box'] = {'visible': True}

            x = list()
            y = list()
            if len(self.trace_names) > trace_idx:
                trace_data['name'] = self.trace_names[trace_idx]
            for group in sorted(self.traces[trace_idx]):
                values = self.traces[trace_idx][group]
                values = self.jitter_and_round(values)
                for value in values:
                    x.append(str(group))
                    y.append(value)

            trace_data['x'] = x
            trace_data['y'] = y
            theplot['data'].append(trace_data)
        theplot['layout'] = dict()
        if len(self.traces) > 1:
            theplot['layout']['violinmode'] = "group"
        if self.title:
            theplot['layout']['title'] = self.title
        if self.ylab:
            theplot['layout']['yaxis'] = dict()
            theplot['layout']['yaxis']['title'] = self.ylab
        if self.units:
            for axis, units in self.units.items():
                axis_name = axis + 'axis'
                theplot['layout'][axis_name] = dict()
                theplot['layout'][axis_name]['title'] = units
        return theplot


class ScatterPlot(object):
    '''
    Class for Plotly scatterplots
    '''
    def __init__(self):
        self.traces = dict()
        self.limits = { 'x': list(), 'y': list()}
        self.units = dict()
    
    def add_trace(self, name):
        if name not in self.traces:
            self.traces[name] = PlotlyTrace(name)
            self.traces[name].order = len(self.traces)
    
    def add_x(self, trace_name, x):
        if trace_name in self.traces:
            self.traces[trace_name].x.append(x)
        else:
            raise(KeyError("Trace %s not found in ScatterPlot!" % trace_name))

    def add_y(self, trace_name, y):
        if trace_name in self.traces:
            self.traces[trace_name].y.append(y)
    
    def add_name(self, trace_name, name):
        if trace_name in self.traces:
            self.traces[trace_name].names.append(name)

    def set_limits(self, axis, start, end):
        if axis == 'x' or axis == 'y':
            self.limits[axis] =[start, end]
        else:
            raise ValueError("Axis should be 'x' or 'y'.")

    def plot(self):
        theplot = dict()
        theplot['data'] = list()
        theplot['layout'] = dict()
        for trace_name in sorted(self.traces.keys(), key=lambda n: self.traces[n].order):
            trace = self.traces[trace_name]
            trace_data = dict()
            if str(trace_name).isdigit():
                trace_data['name'] = 'Cluster ' + str(trace.name)
            else:
                trace_data['name'] = str(trace.name)
            trace_data['x'] = trace.x
            trace_data['y'] = trace.y
            trace_data['type'] = trace.type
            trace_data['mode'] = trace.mode
            if trace.color:
                trace_data['marker'] = { 'color': list(trace.color) }
            if trace.names:
                trace_data['text'] = trace.names
            theplot['data'].append(trace_data)
        theplot['layout'] = {'xaxis': dict(), 'yaxis': dict()}
        if self.limits:
            if 'x' in self.limits:
                theplot['layout']['xaxis']['range'] = self.limits['x']
            if 'y' in self.limits:
                theplot['layout']['yaxis']['range'] = self.limits['y']
        if self.units:
            for axis, units in self.units.items():
                axis_name = axis + 'axis'
                theplot['layout'][axis_name]['title'] = units
        return theplot
    
    def add_color_to_trace(self, trace_name, colors):
        if trace_name in self.traces:
            self.traces[trace_name].color = colors
        else:
            raise(KeyError("Trace %s not found in ScatterPlot!" % trace_name))

    def add_units(self, axis, units):
        '''
        Adds units to one axis of the plot.

        Args:
            axis: string cointaining 'x' or 'y'.
            units: string for units.
        
        Returns:
            nothing
        '''
        if axis == 'x' or axis == 'y':
            self.units[axis] = units
        else:
            raise ValueError("Axis should be a string containing 'x' or 'y'.")


class PlotlyTrace(object):
    '''
    Class for plotly traces
    '''
    def __init__(self, name):
        self.name = name
        self.order = int()
        self.x = list()
        self.y = list()
        self.names = list()
        self.mode = 'markers'
        self.type = 'scatter'
        self.color = list()

    



