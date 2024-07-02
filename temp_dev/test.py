
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QMainWindow
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
 
from pathlib import Path
import sys

site = "https://www.google.com/"
site = 'https://stackoverflow.com/search?q=pyqt5+forcepersistentcookies'

# if site = 'https://stackoverflow.com/search?q=pyqt5+forcepersistentcookies'
# then console output is:
# unset... PersistentCookiesPolicy.AllowPersistentCookies, of the record? : False
# set... PersistentCookiesPolicy.ForcePersistentCookies
# browser_storagefolder : C:/Users/lrpir/.test_cookies, of the record? : False
# js: Error with Feature-Policy header: Unrecognized feature: 'speaker'.
# js: [GSI_LOGGER]: Your client application uses one of the Google One Tap prompt UI status methods that may stop functioning when FedCM becomes mandatory. Refer to the migration guide to update your code accordingly and opt-in to FedCM to test your changes. Learn more: https://developers.google.com/identity/gsi/web/guides/fedcm-migration?s=dc#display_moment and https://developers.google.com/identity/gsi/web/guides/fedcm-migration?s=dc#skipped_moment
# js: [GSI_LOGGER]: Currently, you disable FedCM on Google One Tap. FedCM for One Tap will become mandatory starting Oct 2024, and you wonÆt be able to disable it. Refer to the migration guide to update your code accordingly to ensure users will not be blocked from logging in. Learn more: https://developers.google.com/identity/gsi/web/guides/fedcm-migration
# js: Error with Feature-Policy header: Unrecognized feature: 'speaker'.
# js: [GSI_LOGGER]: Your client application uses one of the Google One Tap prompt UI status methods that may stop functioning when FedCM becomes mandatory. Refer to the migration guide to update your code accordingly and opt-in to FedCM to test your changes. Learn more: https://developers.google.com/identity/gsi/web/guides/fedcm-migration?s=dc#display_moment and https://developers.google.com/identity/gsi/web/guides/fedcm-migration?s=dc#skipped_moment
# js: [GSI_LOGGER]: Currently, you disable FedCM on Google One Tap. FedCM for One Tap will become mandatory starting Oct 2024, and you wonÆt be able to disable it. Refer to the migration guide to update your code accordingly to ensure users will not be blocked from logging in. Learn more: https://developers.google.com/identity/gsi/web/guides/fedcm-migration


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        QMainWindow.__init__(self, *args, **kwargs)
        self.webview = QWebEngineView()

        profile = QWebEngineProfile("savecookies", self.webview)
        print(f"unset... {QWebEngineProfile.persistentCookiesPolicy(profile)}, of the record? : {profile.isOffTheRecord()}") 

        profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        print(f"set... {QWebEngineProfile.persistentCookiesPolicy(profile)}, of the record? : {profile.isOffTheRecord()}")

        browser_storage_folder = Path.home().as_posix() + '/.test_cookies'
        print(f"browser_storagefolder : {browser_storage_folder}")
        
        profile.setPersistentStoragePath(browser_storage_folder)

        self.webpage = QWebEnginePage(profile, self.webview)
        self.webview.setPage(self.webpage)
        self.webview.load(QUrl(site))
        self.setCentralWidget(self.webview)
   
    def closeEvent(self, qclose_event):
        """Overwrite QWidget method so that the folling message does NOT shows on the console :
        "Release of profile requested but WebEnginePage still not deleted. Expect troubles !"
        This is due to the fact that Qt wants QWebEnginePage to be removed first but python removes QWebEngineProfile first.
        So we need to overwrite the closing order and delete QWebEnginePage after """

        # Sets the accept flag of the event object, indicates that the event receiver wants the event.
        qclose_event.accept()
        # Schedules this object for deletion, QObject
        self.webpage.deleteLater()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


# import sys
# from PyQt5 import QtWidgets, QtWebEngineWidgets
# from PyQt5.QtNetwork import QNetworkCookie
# from PyQt5.QtCore import QUrl, QTimer
# from PyQt5.QtGui import QPageLayout, QPageSize
# from PyQt5.QtWidgets import QApplication
# import argparse

# def main(app):
#     url = ''
#     parser = argparse.ArgumentParser(description="Just an example", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
#     parser.add_argument("--url", help="Type url")
#     args = parser.parse_args()
#     config = vars(args)
#     url = config['url']

#     loader = QtWebEngineWidgets.QWebEngineView()
#     profile = QtWebEngineWidgets.QWebEngineProfile("storage", loader)
#     cookie_store = profile.cookieStore()

#     with open('cookie.txt', 'rb') as f:
#         contents = f.read()

#     cookie_store.setCookie(QNetworkCookie(contents))
#     webpage = QtWebEngineWidgets.QWebEnginePage(profile, loader)
#     COOKIPATH = "./Cache" + str(1)
#     # web_profile.setCachePath(COOKIPATH)
#     profile.setPersistentStoragePath(COOKIPATH)
#     profile.setPersistentCookiesPolicy(2)
#     loader.setPage(webpage)
#     loader.setZoomFactor(1)
#     layout = QPageLayout()
#     layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4Extra))
#     layout.setOrientation(QPageLayout.Orientation.Portrait)
#     loader.load(QUrl(url))
#     loader.page().pdfPrintingFinished.connect(lambda *args: QApplication.exit())

#     def emit_pdf(finished):
#         QTimer.singleShot(2000, lambda: loader.page().printToPdf("test.pdf", pageLayout=layout))


#     loader.loadFinished.connect(emit_pdf)
#     app.exec()


# if __name__ == '__main__':
#     app = QtWidgets.QApplication(sys.argv)
#     main(app)


##################################################

# #! /usr/bin/env python

# #Python QtWebEngine Web page Inspector.
# #Saves html to MyInsp.html. Saves page requests to shell and to MyInsp.req
# #Saves web cache at ~/.cache/myinsp
# #Usage: <script.py> <url> | --disable-gpu for nouveau

# import sys, os
# from PyQt5.QtGui import QFont
# from PyQt5.QtCore import Qt, QUrl, pyqtSignal
# from PyQt5.QtNetwork import QNetworkCookie
# from PyQt5.QtWidgets import QWidget, QHBoxLayout, QApplication
# from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
# from PyQt5.QtWebEngineWidgets import (QWebEnginePage, 
#                                 QWebEngineView, QWebEngineSettings)
# #User agents, Desktop, Mobile
# a = ('Mozilla/5.0 (Windows NT 10.0; WOW64; rv:57.0) '
#             'Gecko/20100101 Firefox/57.0')
                        
# b = ('Mozilla/5.0 (iPhone; CPU iPhone OS 10_0_1 like Mac OS X) '
#             'AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 '
#                 'Mobile/14A403 Safari/602.1')

# class BrowserReqIntercept(QWebEngineUrlRequestInterceptor):
#     netS = pyqtSignal(str)    
#     def __init__(self,parent,url,print_request,get_link,req_file):
#         super(BrowserReqIntercept, self).__init__(parent)
#         self.url = url
#         self.print_request = print_request
#         self.get_link = get_link
#         self.req_file = req_file
        
#     #Emit page requests urls
#     def interceptRequest(self,info):
#         t = info.requestUrl()
#         urlLnk = t.url()
#         if self.get_link:
#             if self.get_link in urlLnk:
#                 self.netS.emit(urlLnk)
                
#         #Print requests to shell, spaced
#         if self.print_request:
#             print('\n' + (urlLnk))
            
#         #Write requests to file, spaced    
#         rlist = []
#         if self.req_file:
#             rlist.append(urlLnk)
#             for i in rlist:
#                 with open(self.req_file, 'a') as f:
#                     f.write(i + '\n\n')
                
# class BrowserPage(QWebEnginePage):  
#     link_signal = pyqtSignal(str)
#     link_received = pyqtSignal(str)
#     def __init__(self,url,tmp_dir,html_file,print_request,timeout,
#                 tab_web,parent,get_link,req_file):
#         super(BrowserPage, self).__init__()

#         self.user_agent = (a) #Set user agent here
#         self.tmp_dir = tmp_dir
#         self.html_file = html_file
#         self.req_file = req_file
#         self.timeout = timeout
#         self.tab_web = tab_web
#         self.loadFinished.connect(self._loadFinished) #Connect to signals
#         self.loadProgress.connect(self._loadProgress)
#         self.loadStarted.connect(self._loadstart)
        
#         reqs = BrowserReqIntercept(self,url,print_request,get_link,req_file)
#         def urlnk():
#             return 
#         reqs.netS.connect(urlnk)
#         self.link_received.connect(urlnk)
#         self.profile().setHttpUserAgent(self.user_agent)
#         self.profile().setRequestInterceptor(reqs)
#         self.profile().setCachePath(self.tmp_dir)
#         self.profile().setPersistentStoragePath(self.tmp_dir) 

#     def _loadstart(self):
#         return
        
#     def htm_src(self,source):
#         self.htmlout_file = source
            
#     def _loadProgress(self):
#         self.toHtml(self.htm_src)
        
#     #Write html file after page load
#     def write_html_file(self):
#             with open(self.html_file,'wb') as f:
#                 f.write(self.htmlout_file.encode('utf-8'))
    
#     def _loadFinished(self):
#         print('\n'+'Logging to:'+' '+(str(self.html_file))+' '+
#             (str(self.req_file)))
#         self.write_html_file()
#         if not self.timeout:
#             exit(0)
            
# class BrowserView(QWebEngineView):
#     def __init__(self,url,tmp_dir,html_file,print_request,timeout,
#                 get_link,req_file):
#         super(BrowserView, self).__init__()
        
#         #Set font size, images on/off, scripts on/off
#         self.settings().globalSettings().setFontSize(
#                     QWebEngineSettings.FontSize.MinimumFontSize, (22))
#         self.settings().globalSettings().setAttribute(
#                     QWebEngineSettings.WebAttribute.AutoLoadImages, True)
#         self.settings().globalSettings().setAttribute(
#                     QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        
#         dm = self.url = url
#         if self.url.startswith('http'):
#             dm = self.url.split('/')[2]
#         if dm.startswith('www.'):
#             dm = dm.replace('www.','',1)
            
#         self.domain_name = dm
#         self.tmp_dir = tmp_dir
#         self.html_file = html_file
#         self.get_link = get_link
#         self.print_request = print_request
#         self.req_file = req_file
#         self.timeout = timeout
#         self.Browse(self.url)
        
#     def get_window_object(self):
#         return self.tab_web
    
#     def start_loading(self):
#         self.Browse(self.url)
        
#     def gethtml(self):
#         return self.web.htmlout_file
    
#     def Browse(self,url):
#         self.tab_web = QWidget()
#         self.tab_web.setMinimumSize(1000,800) #Browser window size
#         self.tab_web.show()
#         self.tab_web.setWindowTitle(self.domain_name)
#         self.horizontalLayout_5 = QHBoxLayout(self.tab_web)
#         self.horizontalLayout_5.addWidget(self)
#         self.web = BrowserPage(url,self.tmp_dir,self.html_file,
#         self.print_request,self.timeout,self.tab_web,self,
#         self.get_link,self.req_file)
#         self.setPage(self.web)
#         if self.url is not None:
#             self.load(QUrl(url))
#         QApplication.processEvents()

# def main():
#     app = QApplication(sys.argv)
#     #Path for cache, if not exists make it.
#     tmp_dir = os.path.join(os.path.expanduser('~'),'.cache','myinsp')
#     if not os.path.exists(tmp_dir):
#         os.makedirs(tmp_dir)

#     #Open with arguments or prompt for input, allow --disable-gpu for nouveau 
#     if len(sys.argv) < 2:
#         url = input('Enter/Paste url to Inspect: ')
#     else:
#         url = sys.argv[1]
#     if url.startswith('--'):
#         url = sys.argv[2]
  
#     html_file = 'MyInspect.html'    # html outfile
#     req_file = 'MyInspect.req'  # requests outfile
#     print_request = True    # print requests to shell or not
#     timeout = 1 # 1 for no exit after page load, 0 to exit
    
#     if url.startswith('http'):
#         domain_name = url.split('/')[2]
#     else:
#         domain_name = url
#     domain_name = domain_name.replace('www.','',1)
    
#     get_link = None
#     web = BrowserView(url,tmp_dir,html_file,print_request,timeout,
#         get_link,req_file)
            
#     go = app.exec_()
#     sys.exit(go)

# if __name__ == "__main__":
#     main()