class NetworkInformation {
  constructor() {

  }

  get downlink() {
    return 10.0;
  }

  get effectiveType() {
    return '4g';
  }

  get rtt() {
    let random = Math.random();
    if (random < 0.70)
      return 50;

    if (random < 0.90)
      return 100;

    return 150;
  }

  get saveData() {
    return false
  }

}

module.exports = NetworkInformation;
