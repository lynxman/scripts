#!/usr/bin/env ruby
# This handler creates and resolves prowl incidents
#
# Released under the same terms as Sensu (the MIT license); see LICENSE
# for details.

require 'rubygems' if RUBY_VERSION < '1.9.0'
require 'sensu-handler'
require 'uri'
require 'net/http'
require 'net/https'
require 'json'

class Prowl < Sensu::Handler

  def handle
    config = settings['prowl']

    incident_key = @event['client']['name'] + '/' + @event['check']['name']

    description = @event['check']['notification']
    description ||= [@event['client']['name'], @event['check']['name'], @event['check']['output']].join(' : ')
    host = @event['client']['name']
    entity_id = incident_key
    state_message = description
    begin
      timeout(10) do

        case @event['action']
        when 'create'
          case @event['check']['status']
          when 1
            message_type = 'WARNING'
          else
            message_type = 'CRITICAL'
          end
        when 'resolve'
          message_type = 'RECOVERY'
        end

        incident_key = @event['client']['name'] + ' ' + @event['check']['name']
        incident_description = message_type + ' ' + @event['check']['output']
        event_params = { apikey: config['apikey'],
                         priority: @event['check']['status'],
                         application: 'sensu',
                         event: incident_key,
                         description: incident_description }
        api_params = URI.escape(event_params.map { |k, v| "#{k}=#{v}" }.join('&'))

        uri   = URI("https://api.prowlapp.com/publicapi/add?#{api_params}")
        https = Net::HTTP.new(uri.host, uri.port)

        https.use_ssl = true

        request      = Net::HTTP::Get.new(uri.request_uri)
        response     = https.request(request)

        if response.code == '200'
          puts "prowl -- #{@event['action'].capitalize}'d incident -- #{incident_key}"
        else
          puts "prowl -- failed to #{@event['action']} incident -- #{incident_key}"
          puts "prowl -- response: #{response.inspect}"
        end
      end
    rescue Timeout::Error
      puts 'prowl -- timed out while attempting to ' + @event['action'] + ' a incident -- ' + incident_key
    end
  end

end
