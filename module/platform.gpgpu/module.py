#
# Collective Knowledge (platform - GPGPU)
#
# See CK LICENSE.txt for licensing details
# See CK COPYRIGHT.txt for copyright details
#
# Developer: Grigori Fursin, Grigori.Fursin@cTuning.org, http://fursin.net
#

cfg={}  # Will be updated by CK (meta description of this module)
work={} # Will be updated by CK (temporal data)
ck=None # Will be updated by CK (initialized CK kernel) 

# Local settings

##############################################################################
# Initialize module

def init(i):
    """

    Input:  {}

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """
    return {'return':0}

##############################################################################
# Detect GPGPU

def detect(i):
    """
    Input:  {
              (host_os)              - host OS (detect, if omitted)
              (os) or (target_os)    - OS module to check (if omitted, analyze host)

              (device_id)            - device id if remote (such as adb)
              (skip_device_init)     - if 'yes', do not initialize device
              (print_device_info)    - if 'yes', print extra device info

              (skip_info_collection) - if 'yes', do not collect info (particularly for remote)

              (skip_print_os_info)   - if 'yes', do not print OS info

              (exchange)             - if 'yes', exchange info with some repo (by default, remote-ck)
              (share)                - the same as 'exchange'
              (exchange_repo)        - which repo to record/update info (remote-ck by default)
              (exchange_subrepo)     - if remote, remote repo UOA

              (extra_info)           - extra info about author, etc (see add from CK kernel)
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              features = {
                gpgpu          - GPGPU features (properties), unified
                gpgpu_misc     - assorted GPGPU features (properties), platform dependent
              }
            }

    """

    import os

    o=i.get('out','')

    oo=''
    if o=='con': oo=o

    # Various params
    hos=i.get('host_os','')
    tos=i.get('target_os','')
    if tos=='': tos=i.get('os','')
    tdid=i.get('device_id','')

    sic=i.get('skip_info_collection','')
    sdi=i.get('skip_device_init','')
    pdv=i.get('print_device_info','')

    ex=i.get('exchange','')
    if ex=='': ex=i.get('share','')

    einf=i.get('extra_info','')
    if einf=='': einf={}

    # Get OS info
    import copy
    ii=copy.deepcopy(i)
    ii['out']=oo
    if i.get('skip_print_os_info','')=='yes': ii['out']=''
    ii['action']='detect'
    ii['module_uoa']=cfg['module_deps']['platform.cpu']
    rr=ck.access(ii) # DO NOT USE rr further - will be reused as return !
    if rr['return']>0: return rr

    hos=rr['host_os_uid']
    hosx=rr['host_os_uoa']
    hosd=rr['host_os_dict']

    tos=rr['os_uid']
    tosx=rr['os_uoa']
    tosd=rr['os_dict']

    tbits=tosd.get('bits','')

    tdid=rr['device_id']

    # Some params
    ro=tosd.get('redirect_stdout','')
    remote=tosd.get('remote','')
    win=tosd.get('windows_base','')

    stdirs=tosd.get('dir_sep','')

    dv=''
    if tdid!='': dv=' -s '+tdid

    # Init
    prop={}
    prop_all={}

    target_gpgpu_name=''
    target_gpgpu_vendor=''

    # Get info about GPGPU ######################################################
    if remote=='yes':
       # Get all params
       params={}

       rx=ck.gen_tmp_file({'prefix':'tmp-ck-'})
       if rx['return']>0: return rx
       fn=rx['file_name']

       # Get GPGPU
       x=tosd.get('adb_dumpsys','').replace('$#device#$',dv)
       x=x.replace('$#category#$','SurfaceFlinger')
       x=x.replace('$#redirect_stdout#$', ro)
       x=x.replace('$#output_file#$', fn)

       if o=='con' and pdv=='yes':
          ck.out('')
          ck.out('Receiving all parameters:')
          ck.out('  '+x)

       rx=os.system(x)
       if rx!=0:
          if o=='con':
             ck.out('')
             ck.out('Non-zero return code :'+str(rx)+' - likely failed')
       else:
          # Read and parse file
          rx=ck.load_text_file({'text_file':fn, 'split_to_list':'yes', 'delete_after_read':'yes'})
          if rx['return']>0: return rx
          ll=rx['lst']

          for s in ll:
              s1=s.strip()
              q2=s1.find('GLES: ')
              if q2>=0:
                 x=s1[6:].strip().split(',')

                 if len(x)>0: 
                    target_gpgpu_vendor=x[0].strip()
                    target_gpgpu_name+=target_gpgpu_vendor
                 if len(x)>1: target_gpgpu_name+=' '+x[1].strip()

                 prop['name']=target_gpgpu_name
                 prop['vendor']=target_gpgpu_vendor
                 prop['possibly_related_cpu_name']=''

                 break
    else:
       if win=='yes':
          r=ck.access({'action':'get_from_wmic',
                       'module_uoa':cfg['module_deps']['platform'],
                       'group':'cpu'})
          if r['return']>0: return r
          info_cpu=r['dict']

          target_cpu=info_cpu.get('Name','')

          r=ck.access({'action':'get_from_wmic',
                       'module_uoa':cfg['module_deps']['platform'],
                       'cmd':'path Win32_VideoController get Name'})
          if r['return']>0: return r
          target_gpgpu_name=r['value']

          x=target_gpgpu_name.split(' ')
          if len(x)>0:
             target_gpgpu_vendor=x[0].strip()

          prop['name']=target_gpgpu_name
          prop['vendor']=target_gpgpu_vendor
          prop['possibly_related_cpu_name']=target_cpu

       else:
          # Get devices
          rx=ck.gen_tmp_file({'prefix':'tmp-ck-'})
          if rx['return']>0: return rx
          fn=rx['file_name']

          x='lspci '+ro+' '+fn

          if o=='con':
             ck.out('')
             ck.out('Executing: '+x)

          rx=os.system(x)
          if rx==0:
             # Read and parse file
             rx=ck.load_text_file({'text_file':fn, 'split_to_list':'yes', 'delete_after_read':'yes'})
             if rx['return']==0: 
                ll=rx['lst']

                for q in ll:
                    x1=q.find('VGA ')
                    if x1>=0:
                       x2=q.find(':', x1+1)
                       if x2>=0:
                          target_gpgpu_name=q[x2+1:].strip()
                          break

          x=target_gpgpu_name.split(' ')
          if len(x)>0:
             target_gpgpu_vendor=x[0].strip()

          prop['name']=target_gpgpu_name
          prop['vendor']=target_gpgpu_vendor

    if o=='con' and prop.get('name','')!='':
       ck.out('')
       ck.out('GPGPU name:   '+prop.get('name',''))
       ck.out('GPGPU vendor: '+prop.get('vendor',''))

    # Check frequency via script
    if win!='yes':
       rx=ck.gen_tmp_file({'prefix':'tmp-ck-'})
       if rx['return']>0: return rx
       fn=rx['file_name']

       cmd=tosd.get('script_get_gpgpu_frequency','')
       if cmd!='':
          cmd+=' '+ro+fn

          # Check path to scripts from env
          path_to_scripts=''

          pi_uoa=os.environ.get('CK_PLATFORM_INIT_UOA','')
          if pi_uoa=='':
             dcfg={}
             ii={'action':'load',
                 'module_uoa':cfg['module_deps']['cfg'],
                 'data_uoa':cfg['lcfg_uoa']}
             r=ck.access(ii)
             if r['return']>0 and r['return']!=16: return r
             if r['return']!=16:
                dcfg=r['dict']
                pi_uoa=dcfg.get('platform_init_uoa',{}).get(pi_key,'')

          if pi_uoa!='' and remote!='yes':
             rx=ck.access({'action':'find',
                           'module_uoa':cfg['module_deps']['platform.init'],
                           'data_uoa':pi_uoa})
             if rx['return']>0: return rx
             path_to_scripts=rx['path']

          if path_to_scripts=='':
             path_to_scripts=tosd.get('path_to_scripts','')

          if path_to_scripts!='': cmd=path_to_scripts+stdirs+cmd

          if remote=='yes':
             # Execute script
             cmd=tosd.get('remote_shell','').replace('$#device#$',dv)+' '+cmd

          if o=='con':
             ck.out('')
             ck.out('Trying to read GPGPU frequency:')
             ck.out('  '+cmd)

          rx=os.system(cmd)
          if rx!=0:
             if o=='con':
                ck.out('')
                ck.out('Non-zero return code :'+str(rx)+' - likely failed')
                ck.out('')
          else:
             # Read and parse file
             rx=ck.load_text_file({'text_file':fn, 'split_to_list':'yes', 'delete_after_read':'yes'})
             if rx['return']>0: return rx
             ll=rx['lst']

             cur_freq=''
             freqs=[]

             jl=len(ll)
             for j in range(0,jl):
                 s=ll[j]
                 if s.lower().startswith('*** current GPGPU frequency:'):
                    if (j+1)<jl:
                       cur_freq=ll[j+1]

                 if s.lower().startswith('*** available GPGPU frequencies:'):
                    while s!='' and j<jl:
                       j+=1
                       if j<jl:
                          s=ll[j]
                          if s!='':
                             freqs.append(s)
                    break

             prop['current_freq']=cur_freq
             prop['all_freqs']=freqs

             if o=='con' and cur_freq!='':
                ck.out('')
                ck.out('Current GPGPU frequency:')
                ck.out('  '+str(cur_freq))
                if len(freqs)>0:
                   ck.out('')
                   ck.out('All frequencies:')
                   for q in freqs:
                       ck.out(' '+q)

    fuoa=''
    fuid=''

    # Exchanging info #################################################################
    if ex=='yes':
       if o=='con':
          ck.out('')
          ck.out('Exchanging information with repository ...')

       xn=prop.get('name','')
       if xn=='':
          # Check if exists in configuration

          dcfg={}
          ii={'action':'load',
              'module_uoa':cfg['module_deps']['cfg'],
              'data_uoa':cfg['cfg_uoa']}
          r=ck.access(ii)
          if r['return']>0 and r['return']!=16: return r
          if r['return']!=16:
             dcfg=r['dict']

          dx=dcfg.get('platform_gpgpu_name',{}).get(tos,{})
          x=tdid
          if x=='': x='default'
          xn=dx.get(x,'')

          if (xn=='' and o=='con'):
             r=ck.inp({'text':'Enter your GPGPU name (for example ARM MALI-T860, Nvidia Tesla K80): '})
             xxn=r['string'].strip()

             if xxn!=xn:
                xn=xxn

                if 'platform_gpgpu_name' not in dcfg: dcfg['platform_gpgpu_name']={}
                if tos not in dcfg['platform_gpgpu_name']: dcfg['platform_gpgpu_name'][tos]={}
                dcfg['platform_gpgpu_name'][tos][x]=xn

                ii={'action':'update',
                    'module_uoa':cfg['module_deps']['cfg'],
                    'data_uoa':cfg['cfg_uoa'],
                    'dict':dcfg}
                r=ck.access(ii)
                if r['return']>0: return r

          if xn=='':
             return {'return':1, 'error':'can\'t exchange information where main name is empty'}

          ixn=xn.find(' ')
          if ixn>0: 
             xx=xn[:ixn].strip()
             prop['vendor']=xx
             xn=xn[ixn+1:].strip()

          prop['name']=xn

       er=i.get('exchange_repo','')
       esr=i.get('exchange_subrepo','')
       if er=='': 
          er=ck.cfg['default_exchange_repo_uoa']
          esr=ck.cfg['default_exchange_subrepo_uoa']

       ii={'action':'exchange',
           'module_uoa':cfg['module_deps']['platform'],
           'sub_module_uoa':work['self_module_uid'],
           'repo_uoa':er,
           'data_name':prop.get('name',''),
           'extra_info':einf,
           'all':'yes',
           'dict':{'features':prop}} # Later we should add more properties from prop_all,
                                     # but should be careful to remove any user-specific info
       if esr!='': ii['remote_repo_uoa']=esr
       r=ck.access(ii)
       if r['return']>0: return r

       fuoa=r.get('data_uoa','')
       fuid=r.get('data_uid','')

       prop=r['dict'].get('features',{})

       if o=='con' and r.get('found','')=='yes':
          ck.out('  GPGPU CK entry already exists ('+fuid+') - loading latest meta (features) ...')

    rr={'return':0, 'features':{}}

    rr['features']['gpgpu']=prop
    rr['features']['gpgpu_misc']=prop_all

    if fuoa!='' or fuid!='':
       rr['features']['gpgpu_uoa']=fuoa
       rr['features']['gpgpu_misc_uid']=fuid

    return rr

##############################################################################
# set frequency

def set_freq(i):
    """
    Input:  {
              (host_os)              - host OS (detect, if omitted)
              (os) or (target_os)    - OS module to check (if omitted, analyze host)

              (device_id)            - device id if remote (such as adb)

              (value) = "max" (default)
                        "min"
                        int value
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """

    import os

    o=i.get('out','')
    oo=''
    if o=='con': oo=o

    v=i.get('value','')
    if v=='': v='max'

    # Various params
    hos=i.get('host_os','')
    tos=i.get('target_os','')
    if tos=='': tos=i.get('os','')
    tdid=i.get('device_id','')

    # Get OS info
    import copy
    ii=copy.deepcopy(i)
    ii['out']=''
    ii['action']='detect'
    ii['module_uoa']=cfg['module_deps']['platform.os']
    ii['skip_info_collection']='yes'
    ii['skip_device_init']='yes'
    rr=ck.access(ii)
    if rr['return']>0: return rr

    hos=rr['host_os_uid']
    hosx=rr['host_os_uoa']
    hosd=rr['host_os_dict']

    tos=rr['os_uid']
    tosx=rr['os_uoa']
    tosd=rr['os_dict']

    tbits=tosd.get('bits','')

    tdid=rr['device_id']

    dir_sep=tosd.get('dir_sep','')

    remote=tosd.get('remote','')

    # Prepare scripts
    cmd=''
    if v=='min':
       cmd=tosd.get('script_set_min_gpgpu_freq','')
    elif v=='max':
       cmd=tosd.get('script_set_max_gpgpu_freq','')
    else:
       cmd=tosd.get('script_set_gpgpu_freq','').replace('$#freq#$',str(v))

    if cmd!='':
       path_to_scripts=tosd.get('path_to_scripts','')
       if path_to_scripts!='': cmd=path_to_scripts+dir_sep+cmd

       if o=='con':
          ck.out('')
          ck.out('CMD to set GPGPU frequency:')
          ck.out('  '+cmd)

       # Get all params
       if remote=='yes':
          dv=''
          if tdid!='': dv=' -s '+tdid

          x=tosd.get('remote_shell','').replace('$#device#$',dv)+' '+cmd

          rx=os.system(x)
          if rx!=0:
             if o=='con':
                ck.out('')
                ck.out('Non-zero return code :'+str(rx)+' - likely failed')

       else:
             rx=os.system(cmd)
             if rx!=0:
                if o=='con':
                   ck.out('')
                   ck.out('  Warning: setting frequency possibly failed - return code '+str(rx))

    return {'return':0}

##############################################################################
# viewing entries as html

def show(i):
    """
    Input:  {
              data_uoa
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              html         - generated HTML
            }

    """


    h='<h2>GPGPUs (CUDA/OpenCL) participating in crowd-tuning</h2>\n'

    h+='<i>View/update meta information in <a href="http://github.com/ctuning/ck">CK format</a> via <a href="http://github.com/ctuning/ck-crowdtuning-platforms">GitHub</a> ...</i><br><br>\n'

    h+='<table class="ck_table" border="0" cellpadding="6" cellspacing="0">\n'

    # Check host URL prefix and default module/action
    url0=ck.cfg.get('wfe_url_prefix','')

    h+=' <tr style="background-color:#cfcfff;">\n'
    h+='  <td><b>\n'
    h+='   #\n'
    h+='  </b></td>\n'
    h+='  <td><b>\n'
    h+='   Vendor\n'
    h+='  </b></td>\n'
    h+='  <td><b>\n'
    h+='   Name\n'
    h+='  </b></td>\n'
    h+='  <td><b>\n'
    h+='   <a href="'+url0+'wcid='+work['self_module_uoa']+':">CK UID</a>\n'
    h+='  </b></td>\n'
    h+=' </tr>\n'

    ruoa=i.get('repo_uoa','')
    muoa=work['self_module_uoa']
    duoa=i.get('data_uoa','')

    r=ck.access({'action':'search',
                 'module_uoa':muoa,
                 'data_uoa':duoa,
                 'repo_uoa':ruoa,
                 'add_info':'yes',
                 'add_meta':'yes'})
    if r['return']>0: 
       return {'return':0, 'html':'Error: '+r['error']}

    lst=r['lst']

    num=0
    for q in sorted(lst, key = lambda x: (x.get('meta',{}).get('features',{}).get('vendor','').upper(), \
                                          x.get('meta',{}).get('features',{}).get('name','').upper())):

        num+=1

        duoa=q['data_uoa']
        duid=q['data_uid']

        meta=q['meta']
        ft=meta.get('features',{})
        
        vendor=ft.get('vendor','')
        name=ft.get('name','')

        h+=' <tr>\n'
        h+='  <td valign="top">\n'
        h+='   '+str(num)+'\n'
        h+='  </td>\n'
        h+='  <td valign="top">\n'
        h+='   '+vendor+'\n'
        h+='  </td>\n'
        h+='  <td valign="top">\n'
        h+='   '+name+'\n'
        h+='  </td>\n'
        h+='  <td valign="top">\n'
        h+='   <a href="'+url0+'wcid='+work['self_module_uoa']+':'+duid+'">'+duid+'</a>\n'
        h+='  </td>\n'
        h+=' </tr>\n'


    h+='</table><br><br>\n'

    return {'return':0, 'html':h}
