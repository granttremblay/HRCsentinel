import matplotlib.pyplot as plt


def styleplots():
    """
    Make plots pretty and labels clear.
    """
    plt.style.use('ggplot')

    labelsizes = 15

    plt.rcParams['font.size'] = labelsizes
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['axes.labelsize'] = labelsizes
    plt.rcParams['xtick.labelsize'] = labelsizes
    plt.rcParams['ytick.labelsize'] = labelsizes


def shieldsentinel_plotter(data, xlims=None, ylims=None, log=False, title=None, markersize=1.0,
             rasterized=True, dpi=300, showfig=True, savefig=False, filename="NAME_ME.pdf"):


    # Unpack the data. Yes I know this is redundant but I'm lazy.

    times = data["times"]
    values = data["values"]
    goestimes = data["goestimes"]
    goesrates = data["goesrates"]
    orbit = data["orbit"]
    scs107times = data["scs107times"]


    # make plots pretty
    styleplots()

    goescolor = list(plt.rcParams['axes.prop_cycle'])[1]['color']
    shieldcolor = list(plt.rcParams['axes.prop_cycle'])[0]['color']
    scs107color = list(plt.rcParams['axes.prop_cycle'])[2]['color']
    thresholdcolor = list(plt.rcParams['axes.prop_cycle'])[3]['color']

    ########### THE PLOT GOES HERE ###############

    fig, ax = plt.subplots(figsize=(16,8))

    # Plot SCS 107s as vertical lines marking start times
    for scs107 in scs107times:
        plt.axvline(scs107, linestyle='dashed', lw=2.0, color=scs107color, alpha=1.0)
    # Double plot the Spetembrer Event lines
    plt.axvline(scs107times[-1], linestyle='dashed', lw=2.0, color=scs107color, alpha=1.0, label="SCS 107 Execution")
    # Plot horizontal line showing the SCS 107 threshold for the HRC Shield
    plt.axhline(y=65535, color=thresholdcolor, alpha=1.0, label="SCS 107 Threshold (65,535 cps)")

    # Plot Radzone Passages, only make a label once .
    for i, (entry, exit) in enumerate(zip(orbit["Radzone Entry"], orbit["Radzone Exit"])):
        plt.axvspan(entry, exit, alpha=0.4, color='gray', label="Radzone Passage" if i == 0 else "")

    # Plot the GOES/HRC Estimated rate
    ax.plot_date(goestimes, goesrates, '-', lw=1.0, label="GOES Estimate", color=goescolor, rasterized=rasterized)

    ax.plot_date(times, values, markersize=markersize, color=shieldcolor,
                 label="HRC Shield Rate (2SHEV1RT)", rasterized=rasterized)


    if log is True:
        ax.set_yscale('log')

    if title is not None:
        ax.set_title(title)

    if xlims is not None:
        ax.set_xlim(xlims[0], xlims[1])

    if ylims is not None:
        ax.set_ylim(ylims[0], ylims[1])

    ax.set_ylabel(r'Counts s$^{-1}$')
    ax.set_xlabel('Date')

    ax.legend()

    #ax.set_xlim(dt.datetime(2017,9,3),dt.datetime(2017,9,21))

    if savefig is True:
        print("Saving figure to {}.".format(filename))
        fig.savefig(filename, dpi=dpi, bbox_inches='tight')

    if showfig is True:
        plt.show()

    # Close the plot so you don't eat too much memory when making 100 of these.
    plt.close()
