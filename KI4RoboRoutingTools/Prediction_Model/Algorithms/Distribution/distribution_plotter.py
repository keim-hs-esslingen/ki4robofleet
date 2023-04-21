from .sector_distribution_model import SectorDistributionModel
import matplotlib.pyplot as plt
import seaborn as sns


def plot_heatmaps(model: SectorDistributionModel):
    # plot target distribution, current distribution and difference
    fig, axes = plt.subplots(1, 3, figsize=(20, 10), sharex=True, sharey=True)
    cbar_ax = fig.add_axes([.91, .3, .03, .4])
    sns.heatmap(model.__current_distribution, ax=axes[0], cbar_ax=cbar_ax)
    axes[0].set_title("Current Distribution")
    sns.heatmap(model.__target_distribution, ax=axes[1], cbar_ax=cbar_ax)
    axes[1].set_title("Target Distribution")
    sns.heatmap(model.__target_distribution - model.__current_distribution, ax=axes[2], cbar_ax=cbar_ax)
    axes[2].set_title("Difference")
    vmax = max(axes[i].collections[0].colorbar.vmax for i in range(3))
    vmin = min(axes[i].collections[0].colorbar.vmin for i in range(3))
    # set colorbar limits to be the same for all plots in one line
    for i in range(3):
        axes[i].collections[0].colorbar.vmin = vmin
        axes[i].collections[0].colorbar.vmax = vmax
    fig.suptitle("Distribution Heatmaps - Simulation time: to-do")
    plt.show()
