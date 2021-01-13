import schedule
import time
from doit.doit_cmd import DoitMain

def run_doit():
    print("run doit")
    DoitMain().run("")

# For now, we run the whole task chain every n seconds.
# In future, we will have adapt this to download frequently updated datasaets more often than infrequently ones
# and probably parallelize downloads so that large downloads don't impact frequent quick ones
# And we might skip valdations for frequently updated datasets.
# Perhaps we should only schedule downloads and let doit watch handle subsequent tasks
schedule.every(30).seconds.do(run_doit)

    
while True:
    schedule.run_pending()
    time.sleep(1)
