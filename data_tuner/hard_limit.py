import numpy as np
import pandas as pd
import tkinter
import pygubu
import os 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class hard_limit():
    def __init__(self, 
                 limits = [None, None],
                 alt_values = [None, None], 
                 limit_by_percent=[False, False],
                 altv_by_percent=[False, False],
                 closed_intervals=[False, False]):
        
        self.limits = limits
        self.alt_values = alt_values
        self.limit_by_percent = limit_by_percent
        self.altv_by_percent = altv_by_percent
        self.closed_intervals = closed_intervals

    def transform(self, x):
        if type(x) == pd.Series:
            x = x.copy(deep=True)
        else:
            x = pd.Series(data=x)
        # ensure x is pd.Series
        for i, (_limit, _altv, _lim_by_perc, _altv_by_perc, _ci) in enumerate(
            zip(self.limits, self.alt_values, self.limit_by_percent, 
                self.altv_by_percent, self.closed_intervals)):
            if _limit is None: 
                pass
            else:
                if _lim_by_perc:
                    assert _limit>=0 and _limit<=1, "'By Percent' is chosen. Expect input between 0 and 1."
                    _limit = x.quantile(_limit)
                if _altv is None:
                    _altv = _limit
                else:
                    if _altv_by_perc:
                        assert _limit>=0 and _limit<=1, "'By Percent' is chosen. Expect input between 0 and 1."
                        _altv = x.quantile(_altv)
#                 print(i)
                if _ci:
                    x[(-1)**i*x<=(-1)**i*_altv] = _altv
                else:
                    x[(-1)**i*x<(-1)**i*_altv] = _altv
        return x
    
    def gui(self, data):
        root = tkinter.Tk()
        app = Application(root, data)
        root.mainloop()




class Application:
    """
    to-do:
        - add vertical mean line in hist plot
        - add bin number tuner
        - UI change:
            - change radio buttons to drop-down menu
            - change threshhold, alter value entries to slide bar
    """
    def __init__(self, master, data=pd.Series(np.random.normal(0,0.1,1000), name='Toy Data (Original)')):
        self.data = data
        self.master = master
        self.base_frame = tkinter.Frame(master)
        #1: Create a builder
        self.builder = builder = pygubu.Builder()

        #2: Load an ui file
        builder.add_from_file(os.path.join(os.path.dirname(__file__), 'hard_limit_gui.ui'))

        #3: Create the widget using a master as parent
        self.main_frame = builder.get_object('main_frame', self.base_frame)
        self.main_frame.pack(side="left")
#         # + Configure layout of the master. Set master resizable:
        builder.connect_callbacks(self)
        self.base_frame.rowconfigure(0, weight=1)
        self.base_frame.columnconfigure(0, weight=1)
    
        self._rendered = False
        
        self.fig = Figure()
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)

        df = self._compare(s_old=data)
        self.n_bins_default = int(min(max(10, len(self.data/20)), 30))
        self.n_bins = self.n_bins_default

        self.ax1_container = self._get_lines(df)
        self.ax2_container = self._get_hist(df)

        self.viz_canvas = FigureCanvasTkAgg(self.fig,master=self.base_frame)
        self.viz_canvas.get_tk_widget().pack(side="left")
        self.viz_canvas.draw()
        self.base_frame.pack()

        # Initialization
        tk_var_default = {
            'lim1': np.nan, 
            'lim2': np.nan, 
            'altv1': np.nan, 
            'altv2': np.nan,
            'lim_perc1': 'Percent',
            'lim_perc2': 'Percent',
            'bin_num': f"Bin Num: {self.n_bins_default}"
        }
        for k, v in tk_var_default.items():
            self.builder.get_variable(k).set(v)
            
    def _menu_1_sel(self, itemid):
        print(self.builder.get_variable('lim_perc2'))
        if itemid == 'Command_1_1':
            self.builder.get_variable('lim_perc2').set('Value')
        elif itemid == 'Command_1_2':
            self.builder.get_variable('lim_perc2').set('Percent')
        else:
            raise Exception("Error encounter!")
            
    def _menu_2_sel(self, itemid):
        print(self.builder.get_variable('altv_perc2'))
        if itemid == 'Command_2_1':
            self.builder.get_variable('altv_perc2').set('Value')
        elif itemid == 'Command_2_2':
            self.builder.get_variable('altv_perc2').set('Percent')
        else:
            raise Exception("Error encounter!")
            
    def _menu_3_sel(self, itemid):
        if itemid == 'Command_3_1':
            self.builder.get_variable('lim_perc1').set('Value')
        elif itemid == 'Command_3_2':
            self.builder.get_variable('lim_perc1').set('Percent')
        else:
            raise Exception("Error encounter!")
            
    def _menu_4_sel(self, itemid):
        if itemid == 'Command_4_1':
            self.builder.get_variable('altv_perc1').set('Value')
        elif itemid == 'Command_4_2':
            self.builder.get_variable('altv_perc1').set('Percent')
        else:
            raise Exception("Error encounter!")   

    def _update_n_bin(self,scale_value):
        v = int(float(scale_value)/50*self.n_bins_default)
        # print(v)
        self.builder.get_variable('bin_num').set(f"Bin Num: {v}")
        self.n_bins = max(v,1) 
        
    def _fetch_params(self):
        # get data from front end
        def _to_none(x):
            if np.isnan(x):
                return None
            else:
                return x
        limits = [
            _to_none(self.builder.get_variable('lim1').get()),
            _to_none(self.builder.get_variable('lim2').get())
        ]
        
        limit_by_percent = ['perc' in x.lower() for x in [
            self.builder.get_variable('lim_perc1').get(),
            self.builder.get_variable('lim_perc2').get()]
        ]
        
        alt_values = [
            _to_none(self.builder.get_variable('altv1').get()),
            _to_none(self.builder.get_variable('altv2').get())
        ]
                     
        altv_by_percent = ['perc' in x.lower() for x in [
            self.builder.get_variable('altv_perc1').get(),
            self.builder.get_variable('altv_perc2').get()]            
        ]
        closed_intervals = [
            self.builder.get_variable('ci1').get(),
            self.builder.get_variable('ci2').get()  
        ]
        return limits, limit_by_percent, alt_values, altv_by_percent, closed_intervals      
            
    def _compare(self, s_old, s_new=None):
        if s_new is None:
            s_new = s_old
        # diverge data streams
        df = pd.concat([s_old, s_new, s_old-s_new], axis=1, sort=False)
        df.columns = ['old', 'new', 'diff']
        df['both'] = df['old']
        df['old_only'] = df['old']
        df['new_only'] = df['new']
        ind_diff = df[df.iloc[:,2] != 0].index
        ind_same = df[df.iloc[:,2] == 0].index
        df.loc[ind_same,['old_only', 'new_only']] = np.nan
        df.loc[ind_diff, 'both'] = np.nan
        return df.drop(columns=['diff'])
            
    def _remove(self, drop_list=[]):
        for obj in drop_list:
            if obj is None:
                pass
            elif type(obj) == tuple: # hist elements
                cnt, bins, bars = obj
                for b in bars:
                    b.remove()
            else:
                obj.remove()
    
    def _get_lines(self, df):
        # old_only
        x = list(range(df.shape[0]))
        
        s1 = self.ax1.scatter(x, df['old_only'].to_list(), alpha=0.6, c='grey')
        # new_only
        s2 = self.ax1.scatter(x, df['new_only'].to_list(), alpha=0.4, c='green')
        # both
        s3 = self.ax1.scatter(x, df['both'].to_list(), alpha=0.6, c='blue')
        # old
        max_line1 = self.ax1.axhline(y=df['old'].max(), linestyle='dotted', c='black', alpha=0.5)
        min_line1 = self.ax1.axhline(y=df['old'].min(), linestyle='dotted', c='black', alpha=0.5)
        # new
        max_line2 = self.ax1.axhline(y=df['new'].max(), linestyle='dotted', c='orange', alpha=0.5)
        min_line2 = self.ax1.axhline(y=df['new'].min(), linestyle='dotted', c='orange', alpha=0.5)

        return [s1, s2, s3, max_line1, min_line1, max_line2, min_line2]
            
    def _get_hist(self, df):
        # print(self.n_bins)
        bins=np.histogram(np.hstack((df['old'], df['new'])), bins=int(self.n_bins))[1]
        h1 = self.ax2.hist(df['old'], bins=bins, alpha=0.3, color='blue')
        if self._rendered:
            h2 = self.ax2.hist(df['new'], bins=bins, alpha=0.6, color='orange')
            return [h1, h2]
        else:
            return [h1]
        

    def render(self):
        self._rendered = True
        limits, limit_by_percent, alt_values, altv_by_percent, closed_intervals = self._fetch_params()
        
        if all([_param is None for _param in limits]):
            if self.n_bins == self.n_bins_default:
                pass
            else:
                df = self._compare(self.data)
                self._remove(drop_list=self.ax2_container)
                self.ax2_container = self._get_hist(df)
                # dim the original plot
                self.viz_canvas.draw()
        else: 
            processor = hard_limit(limits, alt_values, limit_by_percent, altv_by_percent, closed_intervals)
            data_new = processor.transform(self.data)
            df = self._compare(self.data, data_new)
            self._remove(drop_list=self.ax1_container)
            self.ax1_container = self._get_lines(df)
            self._remove(drop_list=self.ax2_container)
            self.ax2_container = self._get_hist(df)
             # dim the original plot
            self.viz_canvas.draw()
        
    def reset(self):
        self.base_frame.destroy()
        self.__init__(master=self.master)
        
    def save(self):
        limits, limit_by_percent, alt_values, altv_by_percent, closed_intervals = self._fetch_params()
        return hard_limit(limits, alt_values, limit_by_percent, altv_by_percent, closed_intervals)

if __name__ == '__main__':
    root = tkinter.Tk()
    app = Application(root)
    root.mainloop()