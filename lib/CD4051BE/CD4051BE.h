class CD4051BE {
  private:
    int _pinA;
    int _pinB;
    int _pinC;

  public:
    CD4051BE(int pinA, int pinB, int pinC);

    void begin();
    void selectChannel(int channel);
    void channelReset();
};