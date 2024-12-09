import RaStanza from './raStanza'
import { validateRequiredFieldsArePresent } from './util'

/**
 * Class representing a hub.txt file.
 * @extends RaStanza
 * @param {(string|string[])} [hubFile=[]] - A hub.txt file as a string
 * @throws {Error} Throws if the first line of the hub.txt file doesn't start
 * with "hub <hub_name>", if it has invalid entries, or is missing required
 * entries
 */
export default class HubFile extends RaStanza {
  protected validate() {
    validateRequiredFieldsArePresent(
      this,
      ['hub', 'shortLabel', 'longLabel', 'genomesFile', 'email'],
      'Hub file',
    )
  }
}
