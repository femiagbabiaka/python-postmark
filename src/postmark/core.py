__version__         = '0.2.0'
__author__          = "Dave Martorana (http://davemartorana.com) & Richard Cooper (http://frozenskys.com)"
__date__            = '2010-April-14'
__url__             = 'http://postmarkapp.com'
__copyright__       = "(C) 2009-2010 David Martorana, Wildbit LLC, Python Software Foundation."
__contributors__    = "Dave Martorana (themartorana), Bill Jones (oraclebill), Richard Cooper (frozenskys)"

#
# Imports (JSON library based on import try)

import sys
import urllib
import urllib2
import httplib

try:
    import json                     
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        raise Exception('Cannot use python-postmark library without Python 2.6 or greater, or Python 2.4 or 2.5 and the "simplejson" library')

#
#
__POSTMARK_URL__ = 'http://api.postmarkapp.com/email'

class PMMail(object):
    '''
    The Postmark Mail object.
    '''
    def __init__(self, **kwargs):
        '''
        Keyword arguments are:
        api_key:        Your Postmark server API key
        sender:         Who the email is coming from, in either
                        "name@email.com" or "First Last <name@email.com>" format
        to:             Who to send the email to, in either
                        "name@email.com" or "First Last <name@email.com>" format
                        Can be multiple values separated by commas (limit 20)
        cc:             Who to copy the email to, in either
                        "name@email.com" or "First Last <name@email.com>" format
                        Can be multiple values separated by commas (limit 20)
        subject:        Subject of the email
        tag:            Use for adding categorizations to your email
        html_body:      Email message in HTML
        text_body:      Email message in plain text
        custom_headers: A dictionary of key-value pairs of custom headers.
        '''
        # initialize properties
        self.__api_key = None
        self.__sender = None
        self.__reply_to = None
        self.__to = None
        self.__cc = None
        self.__subject = None
        self.__tag = None
        self.__html_body = None
        self.__text_body = None
        self.__custom_headers = {}
        #self.__multipart = False
        
        acceptable_keys = (
            'api_key', 
            'from', 
            'reply_to',
            'to', 'recipient', # 'recipient' is legacy
            'cc', 
            'subject', 
            'tag',
            'html_body', 
            'text_body', 
            'custom_headers',
            #'multipart'
        )
        
        for key in kwargs:
            if key in acceptable_keys:
                if key == 'recipient':
                    setattr(self, '_PMMail__to', kwargs[key])
                else:
                    setattr(self, '_PMMail__%s' % key, kwargs[key])
                
        # Set up the user-agent
        self.__user_agent = 'Python/%s (python-postmark library version %s)' % ('_'.join([str(var) for var in sys.version_info]), __version__)
        
        # Try to pull in the API key from Django
        try:
            from django import VERSION
            from django.conf import settings as django_settings
            self.__api_key = django_settings.POSTMARK_API_KEY
            self.__user_agent = '%s (Django %s)' % (self.__user_agent, '_'.join([str(var) for var in VERSION]))
            
            # Allow either POSTMARK_SENDER or POSTMARK_FROM
            self.__sender = getattr(django_settings, 'POSTMARK_SENDER', None)
            self.__sender = getattr(django_settings, 'POSTMARK_FROM', None)
        except ImportError:
            pass
        
    #
    # Properties
    
    def _set_custom_headers(self, value):
        '''
        A special set function to ensure 
        we're setting with a dictionary
        '''
        if value == None:
            setattr(self, '_PMMail__custom_headers', {})
        elif type(value) == dict:
            setattr(self, '_PMMail__custom_headers', value)
        else:
            raise TypeError('Custom headers must be a dictionary of key-value pairs')
    
    
    api_key = property(
        lambda self: self.__api_key,
        lambda self, value: setattr(self, '_PMMail__api_key', value),
        lambda self: setattr(self, '_PMMail__api_key', None), 
        '''
        The API Key for your rack server on Postmark
        '''
    )

    # "from" is a reserved word
    sender = property(
        lambda self: self.__sender,
        lambda self, value: setattr(self, '_PMMail__sender', value),
        lambda self: setattr(self, '_PMMail__sender', None),
        '''        
        The sender, in either "name@email.com" or "First Last <name@email.com>" formats.  
        The address should match one of your Sender Signatures in Postmark.
        Specifying the address in the second fashion will allow you to replace
        the name of the sender as it appears in the recipient's email client.
        '''
    )
        
    reply_to = property(
        lambda self: self.__reply_to,
        lambda self, value: setattr(self, '_PMMail__reply_to', value),
        lambda self: setattr(self, '_PMMail__reply_to', None),
        '''
        A reply-to address, in either "name@email.com" or "First Last <name@email.com>" 
        format. The reply-to address does not have to be one of your Sender Signatures in Postmark.
        This allows a different reply-to address than sender address.
        '''
    )
     
    to = property(
        lambda self: self.__to,
        lambda self, value: setattr(self, '_PMMail__to', value),
        lambda self: setattr(self, '_PMMail__to', None),
        '''
        The recipients, in either "name@email.com" or "First Last <name@email.com>" formats
        '''
    )
    
    cc = property(
        lambda self: self.__cc,
        lambda self, value: setattr(self, '_PMMail__cc', value),
        lambda self: setattr(self, '_PMMail__cc', None),
        '''
        The cc recipients, in either "name@email.com" or "First Last <name@email.com>" formats
        '''
    )
    
    subject = property(
        lambda self: self.__subject,
        lambda self, value: setattr(self, '_PMMail__subject', value),
        lambda self: setattr(self, '_PMMail__subject', None),
        '''
        The subject of your email message
        '''
    )

    tag = property(
        lambda self: self.__tag,
        lambda self, value: setattr(self, '_PMMail__tag', value),
        lambda self: setattr(self, '_PMMail__tag', None),
        '''
        You can categorize outgoing email using the optional Tag property. 
        If you use different tags for the different types of emails your application generates, 
        you will be able to get detailed statistics for them through the Postmark user interface.
        '''
    )
    
    html_body = property(
        lambda self: self.__html_body,
        lambda self, value: setattr(self, '_PMMail__html_body', value),
        lambda self: setattr(self, '_PMMail__html_body', None),
        '''
        The email message body, in html format
        '''
    )
    
    text_body = property(
        lambda self: self.__text_body,
        lambda self, value: setattr(self, '_PMMail__text_body', value),
        lambda self: setattr(self, '_PMMail__text_body', None),
        '''
        The email message body, in text format
        '''
    )
    
    custom_headers = property(
        lambda self: self.__custom_headers,
        _set_custom_headers, 
        lambda self: setattr(self, '_PMMail__custom_headers', {}),
        '''
        Custom headers in a standard dictionary. 
        NOTE: To change the reply to address, use the .reply_to
        property instead of a custom header.
        '''
    )
    
#     multipart = property(
#         lambda self: self.__multipart,
#         lambda self, value: setattr(self, '_PMMail__multipart', value),
#         'The API Key for one of your servers on Postmark'
#     )
        

    #####################
    #
    # LEGACY SUPPORT 
    #
    #####################
    
    recipient = property(
        lambda self: self.__to,
        lambda self, value: setattr(self, '_PMMail__to', value),
        lambda self: setattr(self, '_PMMail__to', None),
        '''
        The recipients, in either "name@email.com" or "First Last <name@email.com>" formats
        '''
    )

    #####################
    #
    # END LEGACY SUPPORT 
    #
    #####################


    
    def _check_values(self):
        '''
        Make sure all values are of the appropriate
        type and are not missing.
        '''
        if not self.__api_key:
            raise PMMailMissingValueException('Cannot send an e-mail without a Postmark API Key')
        elif not self.__sender:
            raise PMMailMissingValueException('Cannot send an e-mail without a sender (.from field)')
        elif not self.__to:
            raise PMMailMissingValueException('Cannot send an e-mail without at least one recipient (.to field)')
        elif not self.__subject:
            raise PMMailMissingValueException('Cannot send an e-mail without a subject')
        elif not self.__html_body and not self.__text_body:
            raise PMMailMissingValueException('Cannot send an e-mail without either an HTML or text version of your e-mail body')

    
    def send(self, test=False):
        '''
        Send the email through the Postmark system.  
        Pass test=True to just print out the resulting
        JSON message being sent to Postmark
        '''
        self._check_values()
        
        # Set up message dictionary
        json_message = {
            'From':     self.__sender,
            'To':       self.__to,
            'Subject':  self.__subject,
        }
        
        if self.__reply_to:
            json_message['ReplyTo'] = self.__reply_to
        
        if self.__cc:
            json_message['Cc'] = self.__cc

        if self.__tag:
            json_message['Tag'] = self.__tag
        
        if self.__html_body:
            json_message['HtmlBody'] = self.__html_body
            
        if self.__text_body:
            json_message['TextBody'] = self.__text_body
            
        if len(self.__custom_headers) > 0:
            cust_headers = []
            for key in self.__custom_headers.keys():
                cust_headers.append({
                    'Name': key,
                    'Value': self.__custom_headers[key]
                })
            json_message['Headers'] = cust_headers
            
#         if (self.__html_body and not self.__text_body) and self.__multipart:
#             # TODO: Set up regex to strip html
#             pass
        
        # If this is a test, just print the message
        if test:
            print 'JSON message is:\n%s' % json.dumps(json_message)
            return
            
        
        # Set up the url Request
        req = urllib2.Request(
            __POSTMARK_URL__,
            json.dumps(json_message),
            {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-Postmark-Server-Token': self.__api_key,
                'User-agent': self.__user_agent
            }
        )
        
        # Attempt send
        try:
            #print 'sending request to postmark: %s' % json_message
            result = urllib2.urlopen(req)
            result.close()
            if result.code == 200:
                return True
            else:
                raise PMMailSendException('Return code %d: %s' % (result.code, result.msg))
        except urllib2.HTTPError, err:
            if err.code == 401:
                raise PMMailUnauthorizedException('Sending Unauthorized - incorrect API key.', err)
            elif err.code == 422:
                try:
                    jsontxt = err.read()
                    jsonobj = json.loads(jsontxt)
                    desc = jsonobj['Message']
                except:
                    desc = 'Description not given'
                raise PMMailUnprocessableEntityException('Unprocessable Entity: %s' % desc)
            elif err.code == 500:
                raise PMMailServerErrorException('Internal server error at Postmark. Admins have been alerted.', err)
        except urllib2.URLError, err:
            if hasattr(err, 'reason'):
                raise PMMailURLException('URLError: Failed to reach the server: %s (See "inner_exception" for details)' % err.reason, err)
            elif hasattr(err, 'code'):
                raise PMMailURLException('URLError: %d: The server couldn\'t fufill the request. (See "inner_exception" for details)' % err.code, err)
            else:
                raise PMMailURLException('URLError: The server couldn\'t fufill the request. (See "inner_exception" for details)', err)
                
                

class PMBounceManager(object):
    '''
    The Postmark Bounce object.
    '''
    def __init__(self, **kwargs):
        '''
        Keyword arguments are:
        api_key:        Your Postmark server API key
        '''
        # initialize properties
        self.__api_key = None
        
        
        acceptable_keys = (
            'api_key', 
        )

        for key in kwargs:
            if key in acceptable_keys:
                setattr(self, '_PMBounceManager__%s' % key, kwargs[key])
                
        # Set up the user-agent
        self.__user_agent = 'Python/%s (python-postmark library version %s)' % ('_'.join([str(var) for var in sys.version_info]), __version__)
        
        # Try to pull in the API key from Django
        try:
            from django import VERSION
            from django.conf import settings as django_settings
            self.__api_key = django_settings.POSTMARK_API_KEY
            self.__user_agent = '%s (Django %s)' % (self.__user_agent, '_'.join([str(var) for var in VERSION]))
            self.__sender = django_settings.POSTMARK_SENDER
        except ImportError:
            pass
            
    def _check_values(self):
        '''
        Make sure all values are of the appropriate
        type and are not missing.
        '''
        if not self.__api_key:
            raise PMMailMissingValueException('Cannot check bounces without a Postmark Server API Key')      

    api_key = property(
        lambda self: self.__api_key,
        lambda self, value: setattr(self, '_PMMail__api_key', value),
        lambda self: setattr(self, '_PMMail__api_key', None), 
        '''
        The API Key for your rack server on Postmark
        '''
    )       
    
    def delivery_stats(self):
        '''
        Returns a summary of inactive emails and bounces by type.
        '''
        self._check_values()
        
        req = urllib2.Request(
            __POSTMARK_URL__ + 'deliverystats',
            None,
            {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-Postmark-Server-Token': self.__api_key,
                'User-agent': self.__user_agent
            }
        )
        
        # Attempt send
        try:
            #print 'sending request to postmark:'
            result = urllib2.urlopen(req)
            if result.code == 200:
                return json.loads(result.read())
                result.close()
            else:
            	result.close()
                raise PMMailSendException('Return code %d: %s' % (result.code, result.msg))
            
        except urllib2.HTTPError, err:
            return err
                            
                            
    def get_all(self, inactive='', email_filter='', tag='', count=25, offset=0):
    	'''
        Fetches a portion of bounces according to the specified input criteria. The count and offset 
        parameters are mandatory. You should never retrieve all bounces as that could be excessively 
        slow for your application. To know how many bounces you have, you need to request a portion 
        first, usually the first page, and the service will return the count in the TotalCount property 
        of the response.
        '''
        
        self._check_values()
        
        params = '?inactive=' + inactive + '&emailFilter=' + email_filter +'&tag=' + tag 
        params += '&count=' + str(count) + '&offset=' + str(offset)
        
        req = urllib2.Request(  	
            __POSTMARK_URL__ + 'bounces' + params,
            None,
            {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-Postmark-Server-Token': self.__api_key,
                'User-agent': self.__user_agent
            }
        )
        
        # Attempt send
        try:
            #print 'sending request to postmark:'
            result = urllib2.urlopen(req)
            if result.code == 200:
                return json.loads(result.read())
                result.close()
            else:
            	result.close()
                raise PMMailSendException('Return code %d: %s' % (result.code, result.msg))
            
        except urllib2.HTTPError, err:
            return err
        
        
    def get_single(self, bounce_id):
    	'''
    	Get details about a single bounce. Note that the bounce ID is a numeric value that you 
    	typically obtain after a getting a list of bounces.
    	'''
        self._check_values()
        
        req = urllib2.Request(
            __POSTMARK_URL__ + '/bounces/' + str(bounce_id),
            None,
            {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-Postmark-Server-Token': self.__api_key,
                'User-agent': self.__user_agent
            }
        )
        
        # Attempt send
        try:
            #print 'sending request to postmark:'
            result = urllib2.urlopen(req)
            if result.code == 200:
                return json.loads(result.read())
                result.close()
            else:
            	result.close()
                raise PMMailSendException('Return code %d: %s' % (result.code, result.msg))
            
        except urllib2.HTTPError, err:
            return err
    
    
    def get_dump(self, bounce_id):
        '''
    	Returns the raw source of the bounce Postmark accepted. If Postmark does not have a dump for 
        that bounce, it will return an empty string.
    	'''
        self._check_values()

        req_url = __POSTMARK_URL__ + '/bounces/' + str(bounce_id) + '/dump'
        #print req_url
        
        req = urllib2.Request(
	    req_url,
            None,
            {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-Postmark-Server-Token': self.__api_key,
                'User-agent': self.__user_agent
            }
        )
        
        # Attempt send
        try:
            print 'sending request to postmark:'
            result = urllib2.urlopen(req)
            if result.code == 200:
                return json.loads(result.read())
                result.close()
            else:
            	result.close()
                raise PMMailSendException('Return code %d: %s' % (result.code, result.msg))
            
        except urllib2.HTTPError, err:
            return err
        
    def get_tags(self):
        '''
    	Returns a list of tags used for the current server.
    	'''
        self._check_values()
        
        req = urllib2.Request(
            __POSTMARK_URL__ + 'bounces/tags',
            None,
            {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-Postmark-Server-Token': self.__api_key,
                'User-agent': self.__user_agent
            }
        )
        
        # Attempt send
        try:
            #print 'sending request to postmark:'
            result = urllib2.urlopen(req)
            if result.code == 200:
                return json.loads(result.read())
                result.close()
            else:
            	result.close()
                raise PMMailSendException('Return code %d: %s' % (result.code, result.msg))
            
        except urllib2.HTTPError, err:
            return err
        
    def activate(self, bounce_id):
        '''
    	Activates a deactivated bounce.
    	'''
        self._check_values()
        req_url = '/bounces/' + str(bounce_id) + '/activate'
        #print req_url
        h1 = httplib.HTTPConnection('api.postmarkapp.com')
        dta = urllib.urlencode({"data":"blank"})
        req = h1.request('PUT',
	    req_url,
            dta,
            {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-Postmark-Server-Token': self.__api_key,
                'User-agent': self.__user_agent
            }
        )
	r=h1.getresponse()
	return json.loads(r.read())
        

#
# Exceptions

class PMMailMissingValueException(Exception):
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

class PMMailSendException(Exception):
    '''
    Base Postmark send exception
    '''
    def __init__(self, value, inner_exception=None):
        self.parameter = value
        self.inner_exception = inner_exception
    def __str__(self):
        return repr(self.parameter)

class PMMailUnauthorizedException(PMMailSendException):
    '''
    401: Unathorized sending due to bad API key
    '''
    pass

class PMMailUnprocessableEntityException(PMMailSendException):
    '''
    422: Unprocessable Entity - usually an exception with either the sender
    not having a matching Sender Signature in Postmark.  Read the message
    details for further information
    '''
    pass
    
class PMMailServerErrorException(PMMailSendException):
    '''
    500: Internal error - this is on the Postmark server side.  Errors are
    logged and recorded at Postmark.
    '''
    pass

class PMMailURLException(PMMailSendException):
    '''
    A URLError was caught - usually has to do with connectivity
    and the ability to reach the server.  The inner_exception will
    have the base URLError object.
    '''
    pass




