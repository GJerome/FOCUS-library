import tkinter as tk


w=tk.Tk()
# Set windows parameter
wdth = w.winfo_screenwidth()
hgt = w.winfo_screenheight()
HeightWindow=int(hgt/4)
WidhtWindow=int(wdth/4)
class widget:
    def __init__(self,widht,height,Name,MasterFrame):
        self.Frame=tk.Frame(height=int(height),width=int(widht),master=MasterFrame,relief=tk.GROOVE,borderwidth=2)
        self.Frame.grid(row=0,column=3, padx=5,sticky="nsew")
        self.NameWidget=tk.Label(master=self.Frame, text=Name)
        
        self.Frame.grid(row=0,column=3, padx=5,sticky="nsew")
        self.NameWidget=tk.Label(master=self.Frame, text=Name)

w.geometry("{}x{}".format(WidhtWindow,HeightWindow))

w.minsize(int(wdth/4),int(hgt/4))
w.maxsize(int(wdth),int(hgt))
w.columnconfigure(0, weight=1)
w.columnconfigure(1, weight=1)
w.rowconfigure(0, weight=1)

#Create frame for data and parameter

FrameData=tk.Frame(height=HeightWindow,width=int(WidhtWindow*2/3),master=w,relief=tk.GROOVE,borderwidth=2,bg='red')
FrameData.grid(row=0,column=1, padx=5,sticky="nsew")

FrameParameter=tk.Frame(height=HeightWindow,width=int(WidhtWindow/3),master=w,relief=tk.GROOVE,borderwidth=2,bg='blue')
FrameParameter.grid(row=0,column=0, padx=5,sticky="nsew")

#Now we focus on creating the Scrooll parameter
ScrollParameter=tk.Scrollbar(FrameParameter, orient = 'vertical')
ScrollParameter.pack(fill=tk.Y, side=tk.RIGHT)
t = tk.Text(FrameParameter, width = 15, height = 15, yscrollcommand = ScrollParameter.set)
for i in range(20):
    t.insert(tk.END,"this is some text\n")
t.pack(side=tk.TOP, fill=tk.X)
#ExpositionWidget=tk.Frame(height=50,width=int(wdth),master=FrameParameter,relief=tk.GROOVE,borderwidth=2)
#ExpositionWidget.pack(fill=tk.BOTH, side=tk.LEFT)

#AcquisitionLabel = tk.Label(text="Acquisition",master=ExpositionWidget)
#AcquisitionLabel.pack()

w.mainloop()